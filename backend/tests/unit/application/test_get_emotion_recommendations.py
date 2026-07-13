import pytest
from unittest.mock import Mock

from application.use_cases.get_emotion_recommendations import GetEmotionRecommendations
from domain.entities.emotion import EmotionVector
from domain.entities.movie import Movie
from domain.exceptions import ValidationError


@pytest.fixture
def mock_translator():
    translator = Mock()
    translator.translate_to_english.return_value = "gentle romantic movie"
    return translator


@pytest.fixture
def mock_extractor():
    extractor = Mock()
    # "gentle romantic movie" → high joy, high trust
    extractor.extract.return_value = EmotionVector(joy=0.4, trust=0.3, anticipation=0.2, surprise=0.1)
    return extractor


@pytest.fixture
def mock_emotion_repo():
    repo = Mock()
    # Movies with different emotion profiles
    repo.get_all.return_value = {
        1: EmotionVector(joy=0.5, trust=0.3, anticipation=0.1, surprise=0.1),  # Romantic
        2: EmotionVector(fear=0.5, anger=0.3, sadness=0.1, disgust=0.1),       # Horror
        3: EmotionVector(joy=0.3, trust=0.4, anticipation=0.2, surprise=0.1),  # Romance #2
    }
    repo.get_by_movie_ids.return_value = {
        1: EmotionVector(joy=0.5, trust=0.3, anticipation=0.1, surprise=0.1),
        3: EmotionVector(joy=0.3, trust=0.4, anticipation=0.2, surprise=0.1),
    }
    return repo


@pytest.fixture
def mock_movie_repo():
    repo = Mock()
    repo.get_by_ids.return_value = [
        Movie(id=1, tmdb_id=10, title="Romantic Movie", genres="Romance", cast="", keywords="", overview="", avg_rating=4.0),
        Movie(id=3, tmdb_id=30, title="Love Story", genres="Romance,Drama", cast="", keywords="", overview="", avg_rating=4.5),
        Movie(id=2, tmdb_id=20, title="Horror Film", genres="Horror", cast="", keywords="", overview="", avg_rating=3.5),
    ]
    return repo


@pytest.fixture
def use_case(mock_translator, mock_extractor, mock_emotion_repo, mock_movie_repo):
    return GetEmotionRecommendations(mock_translator, mock_extractor, mock_emotion_repo, mock_movie_repo)


def test_execute_happy_path(use_case, mock_translator):
    results = use_case.execute("phim tình cảm nhẹ nhàng", top_k=2)

    # Should translate query first
    mock_translator.translate_to_english.assert_called_once_with("phim tình cảm nhẹ nhàng")

    # Should return movies sorted by emotion similarity
    # Movie 1 (joy=0.5, trust=0.3) should be most similar to query (joy=0.4, trust=0.3)
    assert len(results) == 2
    assert results[0].movie_id == 1  # Most emotionally similar
    assert results[0].genres == "Romance"


def test_execute_empty_query():
    uc = GetEmotionRecommendations(Mock(), Mock(), Mock(), Mock())
    with pytest.raises(ValidationError):
        uc.execute("")


def test_execute_short_query():
    uc = GetEmotionRecommendations(Mock(), Mock(), Mock(), Mock())
    with pytest.raises(ValidationError):
        uc.execute("ab")


def test_execute_no_emotion_detected(mock_translator, mock_emotion_repo, mock_movie_repo):
    """If NRC can't extract emotions from the query, return empty."""
    extractor = Mock()
    extractor.extract.return_value = EmotionVector()  # All zeros

    uc = GetEmotionRecommendations(mock_translator, extractor, mock_emotion_repo, mock_movie_repo)
    results = uc.execute("xyz qwerty")

    assert results == []


def test_execute_horror_query(mock_translator, mock_emotion_repo, mock_movie_repo):
    """A horror-themed query should match horror movies better."""
    mock_translator.translate_to_english.return_value = "scary terrifying horror"

    extractor = Mock()
    extractor.extract.return_value = EmotionVector(fear=0.5, anger=0.2, surprise=0.2, disgust=0.1)

    uc = GetEmotionRecommendations(mock_translator, extractor, mock_emotion_repo, mock_movie_repo)
    results = uc.execute("phim kinh dị đáng sợ", top_k=3)

    # Movie 2 (fear=0.5, anger=0.3) should be most similar to fear/anger query
    assert len(results) == 3
    assert results[0].movie_id == 2  # Horror movie should rank first
