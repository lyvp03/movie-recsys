from datetime import datetime
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session

from domain.entities.rating import Rating
from infrastructure.db.models import RatingTable
from infrastructure.db.postgres_rating_repo import PostgresRatingRepository


@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)


@pytest.fixture
def repo(mock_session):
    return PostgresRatingRepository(mock_session)


def test_get_by_user(repo, mock_session):
    # Setup
    user_id = 1
    mock_row1 = RatingTable(id=1, user_id=user_id, movie_id=10, rating=4.0, rated_at=datetime.utcnow())
    mock_row2 = RatingTable(id=2, user_id=user_id, movie_id=20, rating=3.5, rated_at=datetime.utcnow())
    
    mock_exec = MagicMock()
    mock_exec.all.return_value = [mock_row1, mock_row2]
    mock_session.exec.return_value = mock_exec

    # Execute
    ratings = repo.get_by_user(user_id)

    # Assert
    assert len(ratings) == 2
    assert isinstance(ratings[0], Rating)
    assert ratings[0].movie_id == 10
    assert ratings[1].movie_id == 20
    
    # Check that exec was called
    mock_session.exec.assert_called_once()


def test_get_all(repo, mock_session):
    mock_row = RatingTable(id=1, user_id=1, movie_id=10, rating=4.0, rated_at=datetime.utcnow())
    
    mock_exec = MagicMock()
    mock_exec.all.return_value = [mock_row]
    mock_session.exec.return_value = mock_exec

    ratings = repo.get_all()
    assert len(ratings) == 1


def test_get_user_rated_movie_ids(repo, mock_session):
    mock_exec = MagicMock()
    mock_exec.all.return_value = [10, 20, 30]
    mock_session.exec.return_value = mock_exec

    movie_ids = repo.get_user_rated_movie_ids(user_id=1)
    
    assert isinstance(movie_ids, set)
    assert len(movie_ids) == 3
    assert {10, 20, 30} == movie_ids


def test_count_by_user(repo, mock_session):
    mock_exec = MagicMock()
    mock_exec.one.return_value = 15
    mock_session.exec.return_value = mock_exec

    count = repo.count_by_user(user_id=1)
    assert count == 15
