import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

def check():
    load_dotenv()
    c = QdrantClient(os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))
    for collection in ["movies_embedding", "movies_tfidf", "movies_emotion"]:
        try:
            count = c.count(collection).count
            print(f"{collection}: {count} points")
        except Exception as e:
            print(f"{collection}: Error - {e}")

if __name__ == "__main__":
    check()
