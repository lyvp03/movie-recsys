import pytest
from unittest.mock import Mock, call

from application.use_cases.get_emotion_recommendations import (
    GetEmotionRecommendations,
    DEFAULT_EMOTION_COLLECTION,
    DEFAULT_EMBEDDING_COLLECTION,
)
from domain.entities.emotion import EmotionVector
from domain.entities.movie import Movie
from domain.exceptions import ValidationError
from domain.interfaces.i_vector_store import SearchResult

def test_execute_happy_path():
    mock_encoder = Mock()
    mock_vector_store = Mock()
    mock_movie_repo = Mock()
    mock_emotion_repo = Mock()
    
    uc = GetEmotionRecommendations(mock_encoder, mock_vector_store, mock_movie_repo, mock_emotion_repo)
    
    mock_encoder.encode.return_value = [0.1, 0.2, 0.3]
    mock_vector_store.search.return_value = [
        SearchResult(id=1, score=0.9, payload={}),
        SearchResult(id=2, score=0.8, payload={})
    ]
    
    mock_movie_repo.get_by_ids.return_value = [
        Movie(id=1, tmdb_id=10, title="Movie 1", genres="Action", cast="", keywords="", overview="", avg_rating=5.0),
        Movie(id=2, tmdb_id=20, title="Movie 2", genres="Drama", cast="", keywords="", overview="", avg_rating=4.0)
    ]
    
    mock_emotion_repo.get_by_movie_ids.return_value = {
        1: EmotionVector(joy=0.8),
        2: EmotionVector(sadness=0.9)
    }
    
    results = uc.execute("happy movie", top_k=2)
    
    assert len(results) == 2
    assert results[0].movie_id == 1
    assert results[0].emotion_tags["joy"] == 0.8
    assert results[1].movie_id == 2
    assert results[1].emotion_tags["sadness"] == 0.9

def test_execute_empty_query():
    uc = GetEmotionRecommendations(Mock(), Mock(), Mock(), Mock())
    with pytest.raises(ValidationError):
        uc.execute("")

def test_execute_fallback():
    mock_encoder = Mock()
    mock_vector_store = Mock()
    mock_movie_repo = Mock()
    mock_emotion_repo = Mock()
    
    uc = GetEmotionRecommendations(mock_encoder, mock_vector_store, mock_movie_repo, mock_emotion_repo)
    
    mock_encoder.encode.return_value = [0.1, 0.2, 0.3]
    
    # First search returns only 1 result, but we asked for top_k=2
    def side_effect(collection, vector, top_k):
        if collection == DEFAULT_EMOTION_COLLECTION:
            return [SearchResult(id=1, score=0.9, payload={})]
        elif collection == DEFAULT_EMBEDDING_COLLECTION:
            return [SearchResult(id=1, score=0.9, payload={}), SearchResult(id=2, score=0.85, payload={})]
        return []
        
    mock_vector_store.search.side_effect = side_effect
    
    mock_movie_repo.get_by_ids.return_value = [
        Movie(id=1, tmdb_id=10, title="Movie 1", genres="Action", cast="", keywords="", overview="", avg_rating=5.0),
        Movie(id=2, tmdb_id=20, title="Movie 2", genres="Drama", cast="", keywords="", overview="", avg_rating=4.0)
    ]
    
    mock_emotion_repo.get_by_movie_ids.return_value = {
        1: EmotionVector(joy=0.8)
        # Movie 2 has no emotion vector (fallback)
    }
    
    results = uc.execute("some query", top_k=2)
    
    assert len(results) == 2
    assert results[0].movie_id == 1
    assert results[1].movie_id == 2
    assert results[1].emotion_tags is None
