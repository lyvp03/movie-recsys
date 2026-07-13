"""Build the emotion index: NRC extraction → Postgres + FastEmbed → Qdrant.

Pipeline:
  1. Load crawled reviews from cache
  2. Extract NRC emotion vectors per movie → save to Postgres
  3. Encode review text with FastEmbed → upsert 384-dim vectors to Qdrant 'movies_emotion'
"""

import json
import logging
import os
import sys
from pathlib import Path

# Add src to python path so we can import from domain, infrastructure, etc.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sqlmodel import Session

from infrastructure.db.connection import get_engine
from infrastructure.db.postgres_emotion_repo import PostgresEmotionRepository
from infrastructure.external.fastembed_encoder import FastEmbedEncoder
from infrastructure.ml.nrc_emotion_extractor import NRCEmotionExtractor
from infrastructure.vector.qdrant_vector_store import QdrantVectorStore

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

REVIEWS_CACHE_FILE = "data/processed/movie_reviews.json"
EMOTION_CACHE_FILE = "data/processed/emotion_embeddings_cache.json"
EMOTION_COLLECTION = os.getenv("QDRANT_COLLECTION_EMOTION", "movies_emotion")

MIN_REVIEW_LENGTH = 10


def load_json(filepath: str) -> dict:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(filepath: str, data: dict) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def setup_qdrant(qdrant_client: QdrantClient) -> None:
    """Recreate the emotion collection for FastEmbed (768-dim vectors)."""
    collections = [c.name for c in qdrant_client.get_collections().collections]
    if EMOTION_COLLECTION in collections:
        logger.info("Deleting existing collection: %s", EMOTION_COLLECTION)
        qdrant_client.delete_collection(EMOTION_COLLECTION)

    logger.info("Creating collection: %s", EMOTION_COLLECTION)
    qdrant_client.create_collection(
        collection_name=EMOTION_COLLECTION,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )


def main() -> None:
    reviews_data = load_json(REVIEWS_CACHE_FILE)
    if not reviews_data:
        logger.error("No reviews found. Run crawl_tmdb_reviews.py first.")
        return

    processed_cache = load_json(EMOTION_CACHE_FILE)

    # Initialize components
    extractor = NRCEmotionExtractor()
    encoder = FastEmbedEncoder()

    qdrant_url = os.getenv("QDRANT_URL", ":memory:")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    if qdrant_url != ":memory:":
        qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    else:
        qdrant_client = QdrantClient(location=":memory:")

    vector_store = QdrantVectorStore(qdrant_client)
    setup_qdrant(qdrant_client)

    session = Session(get_engine())
    emotion_repo = PostgresEmotionRepository(session)

    logger.info("Processing %d movies...", len(reviews_data))

    for i, (movie_id_str, review_text) in enumerate(reviews_data.items()):
        if movie_id_str in processed_cache:
            continue

        movie_id = int(movie_id_str)

        # 1. Extract emotion vector & save to Postgres
        emotion_vector = extractor.extract(review_text)
        emotion_repo.save(movie_id, emotion_vector)

        # 2. Embed the review text for Qdrant
        if len(review_text) > MIN_REVIEW_LENGTH:
            try:
                truncated_text = review_text[:8000]
                vector = encoder.encode(truncated_text)

                vector_store.upsert(
                    EMOTION_COLLECTION,
                    id=movie_id,
                    vector=vector,
                    payload={"movie_id": movie_id},
                )
            except Exception as e:
                logger.error("Error encoding/upserting movie %d: %s", movie_id, e)
                continue

        processed_cache[movie_id_str] = True

        if i > 0 and i % 50 == 0:
            logger.info("Processed %d/%d movies...", i, len(reviews_data))
            save_json(EMOTION_CACHE_FILE, processed_cache)

    # Final save
    save_json(EMOTION_CACHE_FILE, processed_cache)
    logger.info("Done building emotion index.")


if __name__ == "__main__":
    main()
