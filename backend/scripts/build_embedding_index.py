import json
import logging
import math
import os
import sys
import time
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlmodel import Session, select

from application.feature_engineering import build_feature_text
from infrastructure.db.connection import engine
from infrastructure.db.models import MovieTable
from infrastructure.external.gemini_embedding_encoder import GeminiEmbeddingEncoder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

EMBEDDING_COLLECTION = os.getenv("QDRANT_COLLECTION_EMBEDDING", "movies_embedding")
CACHE_FILE = Path("data/processed/embeddings_cache.json")


def load_cache() -> dict[int, list[float]]:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # JSON keys are always strings, map them back to int
                return {int(k): v for k, v in data.items()}
        except Exception as e:
            logger.warning(f"Could not load cache: {e}. Starting fresh.")
    return {}


def save_cache(cache: dict[int, list[float]]):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def main():
    load_dotenv()

    # 1. Init Encoder with API Keys
    keys_str = os.getenv("GEMINI_API_KEYS", "")
    api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    if not api_keys:
        logger.error("No GEMINI_API_KEYS found in environment. Exiting.")
        return

    encoder = GeminiEmbeddingEncoder(api_keys=api_keys)
    logger.info(f"Initialized GeminiEncoder with {len(api_keys)} keys.")

    # 2. Setup Qdrant
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if not qdrant_url or not qdrant_api_key:
        logger.error("Missing QDRANT_URL or QDRANT_API_KEY")
        return

    qdrant_client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        timeout=60.0,
    )

    # Recreate collection
    collections = [c.name for c in qdrant_client.get_collections().collections]
    if EMBEDDING_COLLECTION in collections:
        logger.info(f"Deleting existing collection: {EMBEDDING_COLLECTION}")
        qdrant_client.delete_collection(EMBEDDING_COLLECTION)

    logger.info(f"Creating collection: {EMBEDDING_COLLECTION}")
    qdrant_client.create_collection(
        collection_name=EMBEDDING_COLLECTION,
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
    )

    # 3. Load all movies
    logger.info("Loading movies from database...")
    with Session(engine) as session:
        movies = session.exec(select(MovieTable)).all()
        logger.info(f"Loaded {len(movies)} movies.")

    # 4. Load cache
    cache = load_cache()
    logger.info(f"Loaded {len(cache)} embeddings from cache.")

    # 5. Determine which movies need encoding
    to_encode_movies = []
    for m in movies:
        if m.id not in cache:
            to_encode_movies.append(m)

    logger.info(f"{len(to_encode_movies)} movies need to be encoded.")

    # 6. Encode in batches
    batch_size = 100
    for i in range(0, len(to_encode_movies), batch_size):
        batch = to_encode_movies[i : i + batch_size]
        texts = [build_feature_text(m) for m in batch]

        logger.info(f"Encoding batch {i // batch_size + 1}/{(len(to_encode_movies) - 1) // batch_size + 1}...")
        
        try:
            embeddings = encoder.encode_batch(texts, batch_size=batch_size)
            for m, emb in zip(batch, embeddings):
                cache[m.id] = emb

            # Save cache after every batch
            save_cache(cache)
        except Exception as e:
            logger.error(f"Error encoding batch: {e}")
            logger.info("Saving cache and exiting. Please rerun to resume.")
            save_cache(cache)
            raise

    # 7. Upsert to Qdrant in batches
    logger.info("Upserting vectors to Qdrant...")
    points = []
    for m in movies:
        vector = cache.get(m.id)
        if not vector:
            continue
            
        payload = {
            "movie_id": m.id,
            "tmdb_id": m.tmdb_id,
            "title": m.title,
            "genres": m.genres,
            "avg_rating": m.avg_rating,
        }
        points.append(PointStruct(id=m.id, vector=vector, payload=payload))

    upsert_batch_size = 50
    upserted_count = 0
    for i in range(0, len(points), upsert_batch_size):
        batch_points = points[i : i + upsert_batch_size]
        try:
            qdrant_client.upsert(
                collection_name=EMBEDDING_COLLECTION,
                points=batch_points,
            )
            upserted_count += len(batch_points)
            if upserted_count % 500 == 0:
                logger.info(f"Upserted {upserted_count}/{len(points)} points...")
        except Exception as e:
            logger.error(f"Error upserting batch starting at {i}: {e}")
            # Do not exit immediately, try next batch or sleep
            time.sleep(2)

    logger.info(f"Successfully upserted {upserted_count} vectors into '{EMBEDDING_COLLECTION}'.")


if __name__ == "__main__":
    main()
