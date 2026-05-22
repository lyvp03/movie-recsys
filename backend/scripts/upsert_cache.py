import json
import os
import sys
import time

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sqlmodel import Session, select

sys.path.append('src')
from infrastructure.db.connection import engine
from infrastructure.db.models import MovieTable

def main():
    load_dotenv()
    qdrant = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'), timeout=60)
    
    try:
        with open('data/processed/embeddings_cache.json', 'r') as f:
            cache = {int(k): v for k, v in json.load(f).items()}
    except Exception:
        cache = {}

    print(f'Found {len(cache)} items in cache.')

    with Session(engine) as session:
        movies = {m.id: m for m in session.exec(select(MovieTable)).all()}

    points = []
    for mid, vector in cache.items():
        if mid in movies:
            m = movies[mid]
            payload = {
                'movie_id': m.id,
                'tmdb_id': m.tmdb_id,
                'title': m.title,
                'genres': m.genres,
                'avg_rating': m.avg_rating,
            }
            points.append(PointStruct(id=m.id, vector=vector, payload=payload))

    if points:
        batch_size = 50
        upserted_count = 0
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            try:
                qdrant.upsert(collection_name='movies_embedding', points=batch)
                upserted_count += len(batch)
                print(f"Upserted {upserted_count}/{len(points)}")
            except Exception as e:
                print(f"Error at {i}: {e}")
                time.sleep(2)
                
        print(f'Successfully upserted {upserted_count} vectors to Qdrant.')

if __name__ == "__main__":
    main()
