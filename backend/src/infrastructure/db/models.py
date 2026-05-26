from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel


class UserTable(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    ratings: list["RatingTable"] = Relationship(back_populates="user")


class MovieTable(SQLModel, table=True):
    __tablename__ = "movies"

    id: Optional[int] = Field(default=None, primary_key=True)
    tmdb_id: int = Field(nullable=False)
    title: str = Field(nullable=False)
    genres: str = Field(nullable=False)  # Comma-separated VARCHAR
    cast: str = Field(nullable=False)  # Comma-separated VARCHAR
    keywords: str = Field(nullable=False)  # Comma-separated VARCHAR
    overview: str = Field(nullable=False)
    avg_rating: float = Field(default=0.0, nullable=False)

    # Relationships
    ratings: list["RatingTable"] = Relationship(back_populates="movie")
    emotion_vector: Optional["EmotionVectorTable"] = Relationship(
        back_populates="movie"
    )

    __table_args__ = (Index("idx_movies_tmdb_id", "tmdb_id", unique=True),)


class RatingTable(SQLModel, table=True):
    __tablename__ = "ratings"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    movie_id: int = Field(foreign_key="movies.id", nullable=False)
    rating: float = Field(nullable=False)
    rated_at: datetime = Field(nullable=False)

    # Relationships
    user: UserTable = Relationship(back_populates="ratings")
    movie: MovieTable = Relationship(back_populates="ratings")

    __table_args__ = (
        Index("idx_ratings_user_id", "user_id"),
        Index("idx_ratings_movie_id", "movie_id"),
        Index("idx_ratings_rated_at", "rated_at"),
    )


class EmotionVectorTable(SQLModel, table=True):
    __tablename__ = "emotion_vectors"

    id: Optional[int] = Field(default=None, primary_key=True)
    movie_id: int = Field(foreign_key="movies.id", nullable=False)
    joy: float = Field(default=0.0, nullable=False)
    trust: float = Field(default=0.0, nullable=False)
    fear: float = Field(default=0.0, nullable=False)
    surprise: float = Field(default=0.0, nullable=False)
    sadness: float = Field(default=0.0, nullable=False)
    disgust: float = Field(default=0.0, nullable=False)
    anger: float = Field(default=0.0, nullable=False)
    anticipation: float = Field(default=0.0, nullable=False)

    # Relationships
    movie: MovieTable = Relationship(back_populates="emotion_vector")

    __table_args__ = (Index("idx_emotion_vectors_movie_id", "movie_id", unique=True),)
