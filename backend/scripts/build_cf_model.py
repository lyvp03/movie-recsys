import os
import sys
import pickle
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from infrastructure.db.connection import get_session
from infrastructure.db.postgres_rating_repo import PostgresRatingRepository
from infrastructure.ml.custom_svd_model import MatrixFactorizationSVD


def main():
    load_dotenv()
    
    print("Fetching ratings from PostgreSQL...")
    session_gen = get_session()
    session = next(session_gen)
    
    repo = PostgresRatingRepository(session)
    ratings = repo.get_all()
    
    if not ratings:
        print("No ratings found in the database. Exiting.")
        return

    # Convert to list of (user_id, movie_id, rating)
    training_data = [(r.user_id, r.movie_id, r.rating) for r in ratings]
    print(f"Loaded {len(training_data)} ratings.")

    print("Training Custom SVD Model (Matrix Factorization)...")
    # Initialize our custom SGD model
    model = MatrixFactorizationSVD(n_factors=50, n_epochs=20, lr=0.005, reg=0.02)
    model.fit(training_data)
    
    print("Training completed.")

    # Save to disk
    output_path = Path("data/processed/cf_model.pkl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "wb") as f:
        pickle.dump(model, f)
        
    print(f"Model saved to {output_path}")


if __name__ == "__main__":
    main()
