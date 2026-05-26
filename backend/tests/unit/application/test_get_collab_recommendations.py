from unittest.mock import MagicMock

import pytest

from application.use_cases.get_collab_recommendations import GetCollabRecommendations
from domain.entities.movie import Movie
from domain.exceptions import DomainError


@pytest.fixture
def mock_movie_repo():
    return MagicMock()


@pytest.fixture
def mock_rating_repo():
    return MagicMock()


@pytest.fixture
def mock_cf_model():
    return MagicMock()


@pytest.fixture
def use_case(mock_movie_repo, mock_rating_repo, mock_cf_model):
    return GetCollabRecommendations(mock_movie_repo, mock_rating_repo, mock_cf_model)


def test_execute_success(use_case, mock_movie_repo, mock_rating_repo, mock_cf_model):
    # Setup
    user_id = 1
    mock_rating_repo.get_user_rated_movie_ids.return_value = {10}

    # get_all_ids returns lightweight ID list
    mock_movie_repo.get_all_ids.return_value = [10, 20, 30]

    # get_by_ids returns full entities for top-k enrichment
    mock_movie_repo.get_by_ids.return_value = [
        Movie(id=30, tmdb_id=300, title="C", genres="Drama", cast="", keywords="", overview="", avg_rating=4.5),
        Movie(id=20, tmdb_id=200, title="B", genres="Comedy", cast="", keywords="", overview="", avg_rating=3.5),
    ]

    # Candidates will be 20 and 30
    mock_cf_model.get_top_n.return_value = [(30, 4.8), (20, 3.9)]

    # Execute
    results = use_case.execute(user_id=user_id, top_k=2)

    # Assert
    assert len(results) == 2
    assert results[0].movie_id == 30
    assert results[0].similarity_score == 4.8
    assert results[1].movie_id == 20
    assert results[1].similarity_score == 3.9

    mock_cf_model.get_top_n.assert_called_once_with(user_id, [20, 30], 2)


def test_execute_invalid_top_k(use_case):
    with pytest.raises(DomainError):
        use_case.execute(user_id=1, top_k=0)


def test_execute_no_candidates(use_case, mock_movie_repo, mock_rating_repo, mock_cf_model):
    # User has rated all movies
    mock_rating_repo.get_user_rated_movie_ids.return_value = {10, 20}
    mock_movie_repo.get_all_ids.return_value = [10, 20]

    results = use_case.execute(user_id=1)

    assert results == []
    mock_cf_model.get_top_n.assert_not_called()
