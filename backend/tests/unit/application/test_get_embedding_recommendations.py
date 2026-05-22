import pytest
from unittest.mock import MagicMock

from domain.entities.movie import Movie
from domain.exceptions import EntityNotFoundError
from domain.interfaces.i_vector_store import SearchResult
from application.use_cases.get_embedding_recommendations import GetEmbeddingRecommendations
from application.dtos import RecommendationDTO


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    
    # Mock some movies
    movie1 = Movie(1, 101, "Movie A", "Action", "Cast A", "Key A", "Desc A", 4.0)
    movie2 = Movie(2, 102, "Movie B", "Action", "Cast B", "Key B", "Desc B", 3.5)
    movie3 = Movie(3, 103, "Movie C", "Comedy", "Cast C", "Key C", "Desc C", 4.5)
    
    def get_by_id(mid):
        if mid == 1: return movie1
        elif mid == 2: return movie2
        elif mid == 3: return movie3
        raise EntityNotFoundError(f"Movie {mid} not found")
        
    repo.get_by_id.side_effect = get_by_id
    
    def get_by_ids(mids):
        all_movies = {1: movie1, 2: movie2, 3: movie3}
        return [all_movies[mid] for mid in mids if mid in all_movies]
        
    repo.get_by_ids.side_effect = get_by_ids
    return repo


@pytest.fixture
def mock_vector_store():
    store = MagicMock()
    # Mock get_vector
    store.get_vector.return_value = [0.1, 0.2]
    
    # Mock search to return 3 results, including the queried movie itself
    store.search.return_value = [
        SearchResult(1, 1.0, {}),  # Self
        SearchResult(2, 0.9, {}),
        SearchResult(3, 0.8, {})
    ]
    return store


@pytest.fixture
def use_case(mock_repo, mock_vector_store):
    return GetEmbeddingRecommendations(mock_repo, mock_vector_store)


def test_execute_success(use_case, mock_repo, mock_vector_store):
    results = use_case.execute(1, top_k=2)
    
    # It should ask for vector of movie 1 from movies_embedding collection
    mock_vector_store.get_vector.assert_called_once_with("movies_embedding", 1)
    
    # It should ask for top_k + 1
    mock_vector_store.search.assert_called_once_with(
        collection="movies_embedding", vector=[0.1, 0.2], top_k=3
    )
    
    # It should return 2 results (Movie 2 and Movie 3)
    assert len(results) == 2
    assert isinstance(results[0], RecommendationDTO)
    assert results[0].movie_id == 2
    assert results[0].similarity_score == 0.9


def test_execute_movie_not_found(use_case):
    with pytest.raises(EntityNotFoundError, match="Movie 999 not found"):
        use_case.execute(999)
