import os
import sys

from dotenv import load_dotenv

# Load env variables from .env
load_dotenv()

# Add backend/src to pythonpath dynamically so it can resolve infrastructure modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from infrastructure.db.connection import get_session  # noqa: E402
from sqlalchemy import text  # noqa: E402


def verify_postgres() -> bool:
    print("1. Testing PostgreSQL connection...")
    try:
        session = next(get_session())
        result = session.execute(text("SELECT 1")).scalar()
        if result == 1:
            print("   [OK] PostgreSQL connection succeeded.")
            return True
        else:
            print("   [FAIL] PostgreSQL connection returned unexpected result.")
            return False
    except Exception as e:
        print(f"   [FAIL] PostgreSQL connection failed: {e}")
        return False


def verify_qdrant() -> bool:
    print("\n2. Testing Qdrant Cloud connection...")
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_key = os.getenv("QDRANT_API_KEY")

    if not qdrant_url:
        print("   [FAIL] QDRANT_URL environment variable is missing.")
        return False

    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
        # Fetch collections to verify credentials
        collections_response = client.get_collections()
        col_names = [c.name for c in collections_response.collections]
        print(
            "   [OK] Qdrant Cloud connection succeeded. "
            f"Existing collections: {col_names}"
        )
        return True
    except Exception as e:
        print(f"   [FAIL] Qdrant Cloud connection failed: {e}")
        return False


def verify_gemini() -> bool:
    print("\n3. Testing Gemini API Embedding Encoding...")
    gemini_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")

    if not gemini_key:
        print("   [FAIL] GEMINI_API_KEY environment variable is missing.")
        return False

    try:
        import google.generativeai as genai

        genai.configure(api_key=gemini_key)

        response = genai.embed_content(
            model=model_name,
            content="A stunning sci-fi masterpiece in deep space,",
            task_type="retrieval_document",
        )

        if "embedding" in response:
            vector = response["embedding"]
            print(
                "   [OK] Gemini API embedding succeeded. "
                f"Encoded vector shape: [{len(vector)}]"
            )
            return True
        else:
            print("   [FAIL] Gemini API response does not contain 'embedding' field.")
            return False
    except Exception as e:
        print(f"   [FAIL] Gemini API embedding failed: {e}")
        return False


def main():
    print("=" * 60)
    print("STARTING MOVIE RECSYS INFRASTRUCTURE WIRE VERIFICATION")
    print("=" * 60)

    pg_ok = verify_postgres()
    qdrant_ok = verify_qdrant()
    gemini_ok = verify_gemini()

    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY:")
    print(f"PostgreSQL : {'OK' if pg_ok else 'FAIL'}")
    print(f"Qdrant     : {'OK' if qdrant_ok else 'FAIL'}")
    print(f"Gemini API : {'OK' if gemini_ok else 'FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
