import os
from typing import Generator

from dotenv import load_dotenv
from sqlmodel import Session, create_engine

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create engine. For PostgreSQL we can configure pool_pre_ping
# to ensure connection freshness.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)


def get_session() -> Generator[Session, None, None]:
    """Dependency generator to retrieve database sessions."""
    with Session(engine) as session:
        yield session
