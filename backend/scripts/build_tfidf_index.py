import os
import sys
import logging
from pathlib import Path

# Add src to python path so we can import from domain, infrastructure, etc.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from sqlmodel import Session
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from infrastructure.db.connection import get_engine
from infrastructure.db.postgres_movie_repo import PostgresMovieRepository
from infrastructure.ml.tfidf_vectorizer import TFIDFVectorizerWrapper
from infrastructure.vector.qdrant_vector_store import QdrantVectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MODEL_PATH = Path(__file__).parent.parent / "data" / "models" / "tfidf_vectorizer.joblib"
TFIDF_COLLECTION = os.getenv("QDRANT_COLLECTION_TFIDF", "movies_tfidf")


from application.feature_engineering import build_feature_text

def main():
    load_dotenv()
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url or not qdrant_api_key:
        logger.warning("QDRANT_URL or QDRANT_API_KEY not set. Using in-memory Qdrant for testing.")
        client = QdrantClient(location=":memory:", timeout=60.0)
    else:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=60.0)
        
    vector_store = QdrantVectorStore(client)
    
    with Session(get_engine()) as session:
        repo = PostgresMovieRepository(session)
        logger.info("Fetching all movies from DB...")
        movies = repo.get_all()
        logger.info(f"Loaded {len(movies)} movies.")
        
        if not movies:
            logger.error("No movies found in database. Run seed_movies.py first.")
            return

        logger.info("Building feature texts...")
        texts = [build_feature_text(m) for m in movies]
        
        logger.info("Fitting TF-IDF vectorizer (max_features=5000)...")
        vectorizer = TFIDFVectorizerWrapper(max_features=5000)
        vectorizer.fit(texts)
        
        dim = vectorizer.get_feature_dim()
        logger.info(f"TF-IDF dimensionality: {dim}")
        
        logger.info(f"Saving model to {MODEL_PATH}")
        vectorizer.save(MODEL_PATH)
        
        logger.info(f"Recreating Qdrant collection '{TFIDF_COLLECTION}'...")
        if client.collection_exists(collection_name=TFIDF_COLLECTION):
            client.delete_collection(collection_name=TFIDF_COLLECTION)
            
        client.create_collection(
            collection_name=TFIDF_COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        
        logger.info("Transforming texts to vectors...")
        vectors = vectorizer.transform(texts)
        
        logger.info("Upserting vectors to Qdrant...")
        # Batch upsert could be optimized with client.upsert directly, but for now we'll do it one by one
        # or use the vector store upsert method. Wait, upserting one by one is very slow.
        # I'll manually batch it.
        from qdrant_client.models import PointStruct
        
        batch_size = 50
        for i in range(0, len(movies), batch_size):
            batch_movies = movies[i : i + batch_size]
            batch_vectors = vectors[i : i + batch_size]
            
            points = []
            for m, vec in zip(batch_movies, batch_vectors):
                points.append(
                    PointStruct(
                        id=m.id,
                        vector=vec,
                        payload={
                            "movie_id": m.id,
                            "tmdb_id": m.tmdb_id,
                            "title": m.title,
                        }
                    )
                )
            
            client.upsert(
                collection_name=TFIDF_COLLECTION,
                points=points
            )
            if (i + batch_size) % 1000 == 0:
                logger.info(f"  Upserted {min(i + batch_size, len(movies))}/{len(movies)}")
                
        logger.info("Index build complete!")


if __name__ == "__main__":
    main()
