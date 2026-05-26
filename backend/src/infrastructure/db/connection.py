import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import Engine
from sqlmodel import Session, create_engine

# Load environment variables from .env
load_dotenv()


def _build_engine() -> Engine:
    """Create the SQLAlchemy engine from DATABASE_URL.

    Lazily called on first use, so unit tests that don't need a DB
    won't crash at import time if DATABASE_URL is missing.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return create_engine(database_url, pool_pre_ping=True, echo=False)


# Lazy singleton — initialized on first access
_engine: Engine | None = None


def get_engine() -> Engine:
    """Return the global engine, creating it on first call."""
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_session() -> Generator[Session, None, None]:
    """Dependency generator to retrieve database sessions."""
    with Session(get_engine()) as session:
        yield session
