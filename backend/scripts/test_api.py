import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from api.main import app

with TestClient(app) as client:
    print("Testing recommendations for movie 19467 (Toy Story)...")
    response = client.get("/recommend/content-tfidf/19467?top_k=5")
    print("Status:", response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        print("\nRecommendations:")
        for item in data:
            print(f" - {item['title']} (Score: {item['similarity_score']:.4f})")
            print(f"   Genres: {item['genres']}")
    else:
        print("Error:", response.text)
