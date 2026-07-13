"""Offline evaluation of all 5 recommendation methods.

Metrics computed:
  - Content-Based (TF-IDF, Embedding): Precision@K, Recall@K, NDCG@K
  - Collaborative Filtering (SVD):     RMSE, MAE, Precision@K, NDCG@K
  - Hybrid (TF-IDF, Embedding):        Precision@K, NDCG@K
  - Emotion:                           Hit Rate@K (genre-based)

Usage:
    cd backend
    python scripts/evaluate_all.py
"""

import json
import logging
import math
import os
import pickle
import sys
import time
from collections import defaultdict
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sqlmodel import Session

from infrastructure.db.connection import get_engine
from infrastructure.db.postgres_movie_repo import PostgresMovieRepository
from infrastructure.db.postgres_rating_repo import PostgresRatingRepository
from infrastructure.db.postgres_emotion_repo import PostgresEmotionRepository
from infrastructure.vector.qdrant_vector_store import QdrantVectorStore
from infrastructure.ml.custom_svd_model import MatrixFactorizationSVD, CustomSVDModel
from infrastructure.ml.nrc_emotion_extractor import NRCEmotionExtractor
from application.use_cases.get_tfidf_recommendations import GetTFIDFRecommendations
from application.use_cases.get_embedding_recommendations import GetEmbeddingRecommendations
from application.use_cases.get_collab_recommendations import GetCollabRecommendations
from application.use_cases.get_hybrid_recommendations import GetHybridRecommendations
from application.use_cases.get_emotion_recommendations import GetEmotionRecommendations

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TOP_K = 10
RELEVANCE_THRESHOLD = 3.5  # Ratings >= this are considered "relevant"
OUTPUT_FILE = Path("data/processed/eval_results.json")

# ─── Metric helpers ───────────────────────────────────────────────────────────

def precision_at_k(recommended_ids: list[int], relevant_ids: set[int], k: int) -> float:
    """Fraction of top-k recommendations that are relevant."""
    top = recommended_ids[:k]
    if not top:
        return 0.0
    hits = sum(1 for rid in top if rid in relevant_ids)
    return hits / len(top)


def recall_at_k(recommended_ids: list[int], relevant_ids: set[int], k: int) -> float:
    """Fraction of relevant items that appear in top-k recommendations."""
    if not relevant_ids:
        return 0.0
    top = recommended_ids[:k]
    hits = sum(1 for rid in top if rid in relevant_ids)
    return hits / len(relevant_ids)


def ndcg_at_k(recommended_ids: list[int], relevant_ids: set[int], k: int) -> float:
    """Normalized Discounted Cumulative Gain @ k."""
    top = recommended_ids[:k]
    dcg = 0.0
    for i, rid in enumerate(top):
        if rid in relevant_ids:
            dcg += 1.0 / math.log2(i + 2)  # i+2 because log2(1)=0

    # Ideal DCG: all relevant items at the top
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))

    return dcg / idcg if idcg > 0 else 0.0


def rmse(predictions: list[tuple[float, float]]) -> float:
    """Root Mean Squared Error. predictions = [(actual, predicted), ...]"""
    if not predictions:
        return 0.0
    return math.sqrt(sum((a - p) ** 2 for a, p in predictions) / len(predictions))


def mae(predictions: list[tuple[float, float]]) -> float:
    """Mean Absolute Error."""
    if not predictions:
        return 0.0
    return sum(abs(a - p) for a, p in predictions) / len(predictions)


# ─── Data preparation ─────────────────────────────────────────────────────────

def prepare_train_test(session: Session):
    """Split ratings into train/test per user (temporal: last 20% of each user's ratings = test)."""
    repo = PostgresRatingRepository(session)
    all_ratings = repo.get_all()

    # Group by user
    user_ratings = defaultdict(list)
    for r in all_ratings:
        user_ratings[r.user_id].append(r)

    train_ratings = []
    test_ratings = []
    user_test_relevant = {}  # user_id → set of movie_ids rated >= THRESHOLD in test

    for uid, ratings in user_ratings.items():
        # Sort by timestamp (oldest first)
        ratings.sort(key=lambda r: r.rated_at)

        split_idx = int(len(ratings) * 0.8)
        if split_idx < 1:
            split_idx = 1

        train = ratings[:split_idx]
        test = ratings[split_idx:]

        train_ratings.extend(train)
        test_ratings.extend(test)

        # Ground truth: relevant movies in test set
        relevant = {r.movie_id for r in test if r.rating >= RELEVANCE_THRESHOLD}
        if relevant:
            user_test_relevant[uid] = relevant

    logger.info(
        "Data split: %d train, %d test, %d users with test relevant items",
        len(train_ratings), len(test_ratings), len(user_test_relevant),
    )
    return train_ratings, test_ratings, user_test_relevant


# ─── Evaluators ───────────────────────────────────────────────────────────────

def evaluate_content_based(
    name: str,
    use_case,
    user_test_relevant: dict[int, set[int]],
    train_user_movies: dict[int, set[int]],
    all_movie_ids: list[int],
    max_users: int = 100,
):
    """Evaluate a content-based recommender using Negative Sampling (100 negatives per user)."""
    logger.info("Evaluating %s...", name)
    import random
    precisions, recalls, ndcgs = [], [], []
    errors = 0
    evaluated_users = 0

    for uid, test_relevant in user_test_relevant.items():
        if evaluated_users >= max_users:
            break

        train_movies = train_user_movies.get(uid, set())
        if not train_movies:
            continue
            
        # Create candidate set: test_relevant + 100 random negatives
        negatives = [mid for mid in all_movie_ids if mid not in test_relevant and mid not in train_movies]
        random.seed(uid) # deterministic
        sampled_negatives = random.sample(negatives, min(100, len(negatives)))
        candidates_set = test_relevant.union(sampled_negatives)

        success = False
        for seed_movie_id in list(train_movies)[:3]:
            try:
                # Get recommendations, but filter to only our candidates
                # To do this, we ask for more recommendations, then filter
                recs = use_case.execute(seed_movie_id, 200)
                rec_ids = [r.movie_id for r in recs if r.movie_id in candidates_set]
                
                # If we didn't get 10 candidates, fill with random ones from candidate set
                if len(rec_ids) < TOP_K:
                    remaining = list(candidates_set - set(rec_ids))
                    random.shuffle(remaining)
                    rec_ids.extend(remaining[:TOP_K - len(rec_ids)])

                p = precision_at_k(rec_ids, test_relevant, TOP_K)
                r = recall_at_k(rec_ids, test_relevant, TOP_K)
                n = ndcg_at_k(rec_ids, test_relevant, TOP_K)

                precisions.append(p)
                recalls.append(r)
                ndcgs.append(n)
                evaluated_users += 1
                success = True
                break
            except Exception as e:
                errors += 1
                continue

        if not success:
            continue

    result = {
        "precision@10": round(sum(precisions) / max(len(precisions), 1), 6),
        "recall@10": round(sum(recalls) / max(len(recalls), 1), 6),
        "ndcg@10": round(sum(ndcgs) / max(len(ndcgs), 1), 6),
        "evaluated_users": len(precisions),
        "errors": errors,
    }
    logger.info("%s results: %s", name, result)
    return result


def evaluate_collaborative(
    train_ratings,
    test_ratings,
    user_test_relevant: dict[int, set[int]],
    movie_repo,
    session: Session,
    max_users: int = 100,
):
    """Evaluate collaborative filtering: RMSE/MAE on rating prediction + ranking metrics."""
    logger.info("Evaluating Collaborative Filtering (SVD)...")

    # 1. Train a fresh SVD on train set
    training_data = [(r.user_id, r.movie_id, r.rating) for r in train_ratings]
    model = MatrixFactorizationSVD(n_factors=50, n_epochs=20, lr=0.005, reg=0.02)
    model.fit(training_data)

    # 2. Rating prediction accuracy
    predictions = []
    for r in test_ratings:
        pred = model.predict(r.user_id, r.movie_id)
        predictions.append((r.rating, pred))

    rmse_val = rmse(predictions)
    mae_val = mae(predictions)

    # 3. Ranking evaluation
    # Build a set of train movie IDs per user for exclusion
    train_user_movies = defaultdict(set)
    for r in train_ratings:
        train_user_movies[r.user_id].add(r.movie_id)

    all_movie_ids = movie_repo.get_all_ids()

    precisions = []
    ndcgs = []
    evaluated = 0

    for uid, test_relevant in user_test_relevant.items():
        if evaluated >= max_users:
            break

        train_movies = train_user_movies[uid]
        # Candidates = test_relevant + 100 negatives
        import random
        negatives = [mid for mid in all_movie_ids if mid not in test_relevant and mid not in train_movies]
        random.seed(uid)
        sampled_negatives = random.sample(negatives, min(100, len(negatives)))
        candidates = list(test_relevant.union(sampled_negatives))

        if not candidates:
            continue

        top_n = model.get_top_n(uid, candidates, TOP_K)
        rec_ids = [mid for mid, _ in top_n]

        precisions.append(precision_at_k(rec_ids, test_relevant, TOP_K))
        ndcgs.append(ndcg_at_k(rec_ids, test_relevant, TOP_K))
        evaluated += 1

    result = {
        "rmse": round(rmse_val, 6),
        "mae": round(mae_val, 6),
        "precision@10": round(sum(precisions) / max(len(precisions), 1), 6),
        "ndcg@10": round(sum(ndcgs) / max(len(ndcgs), 1), 6),
        "evaluated_users": len(precisions),
        "rating_predictions": len(predictions),
    }
    logger.info("CF results: %s", result)
    return result, model


def evaluate_hybrid(
    name: str,
    cb_use_case,
    cf_model,
    movie_repo,
    rating_repo,
    user_test_relevant: dict[int, set[int]],
    train_user_movies: dict[int, set[int]],
    all_movie_ids: list[int],
    max_users: int = 100,
):
    """Evaluate hybrid recommender."""
    logger.info("Evaluating %s...", name)

    # Wrap the trained model
    class TempCFModel:
        def __init__(self, model):
            self._model = model
        def predict(self, user_id, movie_id):
            return self._model.predict(user_id, movie_id)
        def get_top_n(self, user_id, movie_ids, n):
            return self._model.get_top_n(user_id, movie_ids, n)

    cf_recommender = GetCollabRecommendations(movie_repo, rating_repo, TempCFModel(cf_model))
    hybrid = GetHybridRecommendations(cb_use_case, cf_recommender, rating_repo)

    precisions = []
    ndcgs = []
    errors = 0
    evaluated = 0

    for uid, test_relevant in user_test_relevant.items():
        if evaluated >= max_users:
            break

        train_movies = train_user_movies.get(uid, set())
        if not train_movies:
            continue

        # Create candidate set: test_relevant + 100 random negatives
        import random
        negatives = [mid for mid in all_movie_ids if mid not in test_relevant and mid not in train_movies]
        random.seed(uid)
        sampled_negatives = random.sample(negatives, min(100, len(negatives)))
        candidates_set = test_relevant.union(sampled_negatives)

        success = False
        for seed_movie_id in list(train_movies)[:3]:
            try:
                recs = hybrid.execute(seed_movie_id, uid, 200)
                rec_ids = [r.movie_id for r in recs if r.movie_id in candidates_set]
                
                # If we didn't get 10 candidates, fill with random ones from candidate set
                if len(rec_ids) < TOP_K:
                    remaining = list(candidates_set - set(rec_ids))
                    random.shuffle(remaining)
                    rec_ids.extend(remaining[:TOP_K - len(rec_ids)])

                precisions.append(precision_at_k(rec_ids, test_relevant, TOP_K))
                ndcgs.append(ndcg_at_k(rec_ids, test_relevant, TOP_K))
                evaluated += 1
                success = True
                break
            except Exception:
                errors += 1
                continue

    result = {
        "precision@10": round(sum(precisions) / max(len(precisions), 1), 6),
        "ndcg@10": round(sum(ndcgs) / max(len(ndcgs), 1), 6),
        "evaluated_users": len(precisions),
        "errors": errors,
    }
    logger.info("%s results: %s", name, result)
    return result


def evaluate_emotion(emotion_repo, movie_repo):
    """Evaluate emotion-based recommendations using genre-matching hit rate."""
    logger.info("Evaluating Emotion-Based...")

    # Test queries with expected genres
    test_queries = [
        ("scary horror movie", {"Horror", "Thriller"}),
        ("romantic love story", {"Romance", "Drama"}),
        ("funny comedy for family", {"Comedy", "Family", "Animation"}),
        ("exciting action adventure", {"Action", "Adventure"}),
        ("sad dramatic film", {"Drama"}),
        ("thrilling suspenseful mystery", {"Thriller", "Mystery", "Crime"}),
        ("heartwarming family movie", {"Family", "Comedy", "Animation"}),
        ("dark and violent crime", {"Crime", "Thriller", "Action"}),
        ("science fiction space adventure", {"Science Fiction", "Adventure"}),
        ("animated movie for children", {"Animation", "Family"}),
        ("war and battle", {"War", "Action", "History"}),
        ("fantasy magical world", {"Fantasy", "Adventure"}),
        ("musical with songs", {"Music", "Musical"}),
        ("inspirational sports story", {"Drama"}),
        ("terrifying psychological horror", {"Horror", "Thriller"}),
        ("sweet romantic comedy", {"Romance", "Comedy"}),
        ("epic historical drama", {"History", "Drama", "War"}),
        ("mystery detective investigation", {"Mystery", "Crime", "Thriller"}),
        ("feel good uplifting movie", {"Comedy", "Drama", "Family"}),
        ("dark dystopian future", {"Science Fiction", "Thriller"}),
    ]

    extractor = NRCEmotionExtractor()

    hits = 0
    total = 0

    for query_text, expected_genres in test_queries:
        try:
            # Extract emotion from query directly (skip translation for eval — query is already English)
            query_emotion = extractor.extract(query_text)
            query_list = query_emotion.to_list()

            if sum(query_list) == 0:
                continue

            # Get all stored emotions
            all_emotions = emotion_repo.get_all()
            if not all_emotions:
                continue

            # Compute cosine similarity
            scored = []
            for movie_id, movie_emotion in all_emotions.items():
                score = query_emotion.cosine_similarity(movie_emotion)
                scored.append((movie_id, score))

            # Fetch movie details to get avg_rating to break ties
            all_mids = [mid for mid, _ in scored]
            movies = movie_repo.get_by_ids(all_mids)
            movie_rating_map = {m.id: m.avg_rating for m in movies}

            # Sort by (score DESC, rating DESC)
            scored.sort(key=lambda x: (x[1], movie_rating_map.get(x[0], 0.0)), reverse=True)
            top_ids = [mid for mid, _ in scored[:TOP_K]]

            # Check if any top result matches expected genres
            hit = False
            for mid in top_ids:
                m = next((m for m in movies if m.id == mid), None)
                if m:
                    movie_genres = set(g.strip() for g in m.genres.split(","))
                    if movie_genres & expected_genres:
                        hit = True
                        break

            if hit:
                hits += 1
            total += 1

        except Exception as e:
            logger.warning("Emotion eval error for '%s': %s", query_text, e)
            continue

    hit_rate = hits / total if total > 0 else 0.0

    result = {
        "hit_rate@10": round(hit_rate, 6),
        "hits": hits,
        "total_queries": total,
    }
    logger.info("Emotion results: %s", result)
    return result


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    start_time = time.time()

    # Setup connections
    session = Session(get_engine())
    movie_repo = PostgresMovieRepository(session)
    rating_repo = PostgresRatingRepository(session)
    emotion_repo = PostgresEmotionRepository(session)

    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    vector_store = QdrantVectorStore(qdrant_client)

    # Data split
    train_ratings, test_ratings, user_test_relevant = prepare_train_test(session)

    # Build train user → highly-rated movie sets (for CB seed selection)
    train_user_movies_high = defaultdict(set)
    for r in train_ratings:
        if r.rating >= RELEVANCE_THRESHOLD:
            train_user_movies_high[r.user_id].add(r.movie_id)

    results = {}

    all_movie_ids = movie_repo.get_all_ids()

    # ── 1. Content-Based TF-IDF ──
    tfidf_uc = GetTFIDFRecommendations(movie_repo, vector_store)
    results["content_tfidf"] = evaluate_content_based(
        "Content-Based TF-IDF", tfidf_uc, user_test_relevant, train_user_movies_high, all_movie_ids
    )

    # ── 2. Content-Based Embedding ──
    embed_uc = GetEmbeddingRecommendations(movie_repo, vector_store)
    results["content_embedding"] = evaluate_content_based(
        "Content-Based Embedding", embed_uc, user_test_relevant, train_user_movies_high, all_movie_ids
    )

    # ── 3. Collaborative Filtering ──
    results["collaborative"], trained_model = evaluate_collaborative(
        train_ratings, test_ratings, user_test_relevant, movie_repo, session
    )

    # ── 4. Hybrid TF-IDF ──
    results["hybrid_tfidf"] = evaluate_hybrid(
        "Hybrid TF-IDF", tfidf_uc, trained_model, movie_repo, rating_repo,
        user_test_relevant, train_user_movies_high, all_movie_ids
    )

    # ── 5. Hybrid Embedding ──
    results["hybrid_embedding"] = evaluate_hybrid(
        "Hybrid Embedding", embed_uc, trained_model, movie_repo, rating_repo,
        user_test_relevant, train_user_movies_high, all_movie_ids
    )

    # ── 6. Emotion ──
    results["emotion"] = evaluate_emotion(emotion_repo, movie_repo)

    # ── Summary ──
    elapsed = time.time() - start_time

    # Thresholds for pass/fail
    thresholds = {
        "content_tfidf": {"precision@10": 0.15, "ndcg@10": 0.20},
        "content_embedding": {"precision@10": 0.20, "ndcg@10": 0.25},
        "collaborative": {"rmse": 0.90, "mae": 0.70, "precision@10": 0.25},
        "hybrid_tfidf": {"precision@10": 0.30, "ndcg@10": 0.35},
        "hybrid_embedding": {"precision@10": 0.30, "ndcg@10": 0.35},
        "emotion": {"hit_rate@10": 0.50},
    }

    print("\n" + "=" * 80)
    print("  EVALUATION RESULTS SUMMARY")
    print("=" * 80)

    for method, metrics in results.items():
        print(f"\n  [{method.upper()}]")
        method_thresholds = thresholds.get(method, {})
        for metric_name, value in metrics.items():
            threshold = method_thresholds.get(metric_name)
            if threshold is not None:
                # For RMSE/MAE, lower is better
                if metric_name in ("rmse", "mae"):
                    passed = value <= threshold
                else:
                    passed = value >= threshold
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"    {metric_name:20s} = {value:10.6f}  (target: {'≤' if metric_name in ('rmse','mae') else '≥'}{threshold})  {status}")
            else:
                print(f"    {metric_name:20s} = {value}")

    print(f"\n  Total evaluation time: {elapsed:.1f}s")
    print("=" * 80)

    # Save results
    output = {
        "results": results,
        "thresholds": thresholds,
        "config": {
            "top_k": TOP_K,
            "relevance_threshold": RELEVANCE_THRESHOLD,
        },
        "elapsed_seconds": round(elapsed, 1),
    }
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info("Results saved to %s", OUTPUT_FILE)

    qdrant_client.close()
    session.close()


if __name__ == "__main__":
    main()
