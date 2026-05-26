import os
import json
import time
import requests
from dotenv import load_dotenv
from sqlmodel import Session, select, func

from infrastructure.db.connection import get_engine
from infrastructure.db.models import MovieTable

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
CACHE_FILE = "data/processed/movie_reviews.json"
MAX_MOVIES = 3000

def get_movies_to_crawl() -> list[MovieTable]:
    with Session(get_engine()) as session:
        # Assuming we want a sample of movies, we just take the first MAX_MOVIES 
        # that have the highest avg_rating or just any MAX_MOVIES.
        statement = select(MovieTable).order_by(MovieTable.id).limit(MAX_MOVIES)
        return session.exec(statement).all()

def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache: dict):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def fetch_reviews(tmdb_id: int) -> list[str]:
    for attempt in range(MAX_RETRIES):
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/reviews"
        params = {"api_key": TMDB_API_KEY, "language": "en-US", "page": 1}

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [review.get("content", "") for review in data.get("results", [])]
            elif response.status_code == 429:
                print(f"Rate limit hit (attempt {attempt + 1}/{MAX_RETRIES}), sleeping {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            else:
                print(f"Failed to fetch for TMDB ID {tmdb_id}: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching reviews for {tmdb_id}: {e}")
            return []

    print(f"Max retries exceeded for TMDB ID {tmdb_id}")
    return []

def main():
    if not TMDB_API_KEY:
        print("Error: TMDB_API_KEY not set in .env")
        return

    movies = get_movies_to_crawl()
    print(f"Found {len(movies)} movies to process.")
    
    cache = load_cache()
    print(f"Loaded {len(cache)} reviews from cache.")
    
    movies_processed = 0
    for movie in movies:
        movie_id_str = str(movie.id)
        if movie_id_str in cache:
            continue
            
        print(f"Fetching reviews for {movie.title} (TMDB: {movie.tmdb_id})...")
        reviews = fetch_reviews(movie.tmdb_id)
        
        # Concat all reviews
        concatenated = " ".join(reviews).strip()
        cache[movie_id_str] = concatenated
        
        movies_processed += 1
        
        # Save periodically to avoid losing data
        if movies_processed % 50 == 0:
            save_cache(cache)
            print(f"Saved cache. Processed {movies_processed} new movies.")
            
        # Respect rate limits (TMDB allows 40 requests per 10 seconds)
        time.sleep(0.3)
        
    save_cache(cache)
    print("Done crawling reviews.")

if __name__ == "__main__":
    main()
