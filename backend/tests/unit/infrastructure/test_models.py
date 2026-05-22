from datetime import datetime

from infrastructure.db.models import (
    EmotionVectorTable,
    MovieTable,
    RatingTable,
    UserTable,
)


def test_user_table_instantiation():
    """Verify that UserTable fields can be set and accessed."""
    user = UserTable(id=1, created_at=datetime(2026, 1, 1))
    assert user.id == 1
    assert user.created_at == datetime(2026, 1, 1)


def test_movie_table_instantiation():
    """Verify that MovieTable fields can be set and accessed."""
    movie = MovieTable(
        id=1,
        tmdb_id=1001,
        title="Inception",
        genres="Sci-Fi,Action",
        cast="Leonardo DiCaprio",
        keywords="dreams,heist",
        overview="A dream within a dream.",
        avg_rating=4.8,
    )
    assert movie.id == 1
    assert movie.tmdb_id == 1001
    assert movie.title == "Inception"
    assert movie.genres == "Sci-Fi,Action"
    assert movie.cast == "Leonardo DiCaprio"
    assert movie.keywords == "dreams,heist"
    assert movie.overview == "A dream within a dream."
    assert movie.avg_rating == 4.8


def test_rating_table_instantiation():
    """Verify that RatingTable fields can be set and accessed."""
    rated_time = datetime(2026, 1, 2, 12, 0, 0)
    rating = RatingTable(id=1, user_id=42, movie_id=1, rating=4.5, rated_at=rated_time)
    assert rating.id == 1
    assert rating.user_id == 42
    assert rating.movie_id == 1
    assert rating.rating == 4.5
    assert rating.rated_at == rated_time


def test_emotion_vector_table_instantiation():
    """Verify that EmotionVectorTable fields can be set and accessed."""
    vector = EmotionVectorTable(
        id=1,
        movie_id=1,
        joy=0.9,
        trust=0.8,
        fear=0.1,
        surprise=0.3,
        sadness=0.0,
        disgust=0.0,
        anger=0.0,
        anticipation=0.6,
    )
    assert vector.id == 1
    assert vector.movie_id == 1
    assert vector.joy == 0.9
    assert vector.trust == 0.8
    assert vector.fear == 0.1
    assert vector.surprise == 0.3
    assert vector.sadness == 0.0
    assert vector.disgust == 0.0
    assert vector.anger == 0.0
    assert vector.anticipation == 0.6
