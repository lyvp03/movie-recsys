from unittest.mock import MagicMock

import pytest

from application.dtos import RecommendationDTO
from application.use_cases.get_hybrid_recommendations import GetHybridRecommendations


@pytest.fixture
def mock_cb_recommender():
    return MagicMock()


@pytest.fixture
def mock_cf_recommender():
    return MagicMock()


@pytest.fixture
def mock_rating_repo():
    return MagicMock()


@pytest.fixture
def use_case(mock_cb_recommender, mock_cf_recommender, mock_rating_repo):
    return GetHybridRecommendations(mock_cb_recommender, mock_cf_recommender, mock_rating_repo)


def test_execute_cold_start_pure_cb(use_case, mock_cb_recommender, mock_cf_recommender, mock_rating_repo):
    # Setup
    mock_rating_repo.count_by_user.return_value = 2  # < 5 ratings -> w_cb=1.0, w_cf=0.0
    
    mock_cb_recommender.recommend.return_value = [
        RecommendationDTO(movie_id=1, tmdb_id=10, title="A", genres="", similarity_score=0.9),
        RecommendationDTO(movie_id=2, tmdb_id=20, title="B", genres="", similarity_score=0.8),
    ]
    
    # Execute
    results = use_case.execute(movie_id=99, user_id=1, top_k=2)
    
    # Assert
    assert len(results) == 2
    assert results[0].movie_id == 1
    assert results[0].similarity_score == 0.9  # 0.9 * 1.0 + 0 * 0.0
    
    mock_cf_recommender.execute.assert_not_called()


def test_execute_warm_start_hybrid(use_case, mock_cb_recommender, mock_cf_recommender, mock_rating_repo):
    # Setup
    mock_rating_repo.count_by_user.return_value = 10  # 5-20 ratings -> w_cb=0.7, w_cf=0.3
    
    # CB returns: 1 (0.8), 2 (0.6)
    mock_cb_recommender.recommend.return_value = [
        RecommendationDTO(movie_id=1, tmdb_id=10, title="A", genres="", similarity_score=0.8),
        RecommendationDTO(movie_id=2, tmdb_id=20, title="B", genres="", similarity_score=0.6),
    ]
    
    # CF returns: 2 (0.9), 3 (0.7)
    mock_cf_recommender.execute.return_value = [
        RecommendationDTO(movie_id=2, tmdb_id=20, title="B", genres="", similarity_score=0.9),
        RecommendationDTO(movie_id=3, tmdb_id=30, title="C", genres="", similarity_score=0.7),
    ]
    
    # Execute
    results = use_case.execute(movie_id=99, user_id=1, top_k=3)
    
    # Calculate expected scores:
    # 1: 0.8 * 0.7 + 0 = 0.56
    # 2: 0.6 * 0.7 + 0.9 * 0.3 = 0.42 + 0.27 = 0.69
    # 3: 0 + 0.7 * 0.3 = 0.21
    
    # Assert order: 2 (0.69), 1 (0.56), 3 (0.21)
    assert len(results) == 3
    assert results[0].movie_id == 2
    assert abs(results[0].similarity_score - 0.69) < 1e-5
    assert results[1].movie_id == 1
    assert abs(results[1].similarity_score - 0.56) < 1e-5
    assert results[2].movie_id == 3
    assert abs(results[2].similarity_score - 0.21) < 1e-5
