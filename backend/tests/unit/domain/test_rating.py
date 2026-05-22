import pytest
from datetime import datetime, timezone

from domain.entities.rating import Rating
from domain.exceptions import InvalidEntityError


def test_rating_creation_success():
    rated_time = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    rating = Rating(
        id=1,
        user_id=42,
        movie_id=862,
        rating=4.5,
        rated_at=rated_time,
    )
    assert rating.id == 1
    assert rating.user_id == 42
    assert rating.movie_id == 862
    assert rating.rating == 4.5
    assert rating.rated_at == rated_time


def test_rating_creation_invalid_rating():
    rated_time = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    
    with pytest.raises(InvalidEntityError, match="Rating must be between 0.5 and 5.0"):
        Rating(
            id=1,
            user_id=42,
            movie_id=862,
            rating=5.5,
            rated_at=rated_time,
        )

    with pytest.raises(InvalidEntityError, match="Rating must be between 0.5 and 5.0"):
        Rating(
            id=1,
            user_id=42,
            movie_id=862,
            rating=0.0,
            rated_at=rated_time,
        )
