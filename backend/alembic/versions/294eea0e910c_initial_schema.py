"""initial_schema

Revision ID: 294eea0e910c
Revises:
Create Date: 2026-05-20 16:48:53.054443

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "294eea0e910c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tables and indexes."""
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. Create movies table
    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tmdb_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("genres", sa.String(), nullable=False),
        sa.Column("cast", sa.String(), nullable=False),
        sa.Column("keywords", sa.String(), nullable=False),
        sa.Column("overview", sa.String(), nullable=False),
        sa.Column("avg_rating", sa.Float(), server_default="0.0", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_movies_tmdb_id", "movies", ["tmdb_id"], unique=True)

    # 3. Create ratings table
    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("rated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["movie_id"],
            ["movies.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ratings_movie_id", "ratings", ["movie_id"], unique=False)
    op.create_index("idx_ratings_user_id", "ratings", ["user_id"], unique=False)
    op.create_index("idx_ratings_rated_at", "ratings", ["rated_at"], unique=False)

    # 4. Create emotion_vectors table
    op.create_table(
        "emotion_vectors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("joy", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("trust", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("fear", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("surprise", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("sadness", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("disgust", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("anger", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("anticipation", sa.Float(), server_default="0.0", nullable=False),
        sa.ForeignKeyConstraint(
            ["movie_id"],
            ["movies.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_emotion_vectors_movie_id", "emotion_vectors", ["movie_id"], unique=True
    )


def downgrade() -> None:
    """Drop tables and indexes."""
    op.drop_index("idx_emotion_vectors_movie_id", table_name="emotion_vectors")
    op.drop_table("emotion_vectors")

    op.drop_index("idx_ratings_rated_at", table_name="ratings")
    op.drop_index("idx_ratings_user_id", table_name="ratings")
    op.drop_index("idx_ratings_movie_id", table_name="ratings")
    op.drop_table("ratings")

    op.drop_index("idx_movies_tmdb_id", table_name="movies")
    op.drop_table("movies")

    op.drop_table("users")
