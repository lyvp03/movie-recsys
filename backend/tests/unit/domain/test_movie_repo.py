import pytest
from typing import Optional

from domain.entities.movie import Movie
from domain.exceptions import EntityNotFoundError
from domain.interfaces.i_movie_repo import IMovieRepository


class InMemoryMovieRepository(IMovieRepository):
    def __init__(self):
        self._movies: dict[int, Movie] = {}

    def save(self, movie: Movie) -> None:
        self._movies[movie.id] = movie

    def get_by_id(self, movie_id: int) -> Movie:
        if movie_id not in self._movies:
            raise EntityNotFoundError(f"Movie {movie_id} not found")
        return self._movies[movie_id]

    def get_all(self) -> list[Movie]:
        return list(self._movies.values())

    def get_by_ids(self, movie_ids: list[int]) -> list[Movie]:
        result = []
        for mid in movie_ids:
            if mid in self._movies:
                result.append(self._movies[mid])
        return result

    def filter_by_genre(self, genre: str) -> list[Movie]:
        return [m for m in self._movies.values() if genre.lower() in m.genres.lower()]


@pytest.fixture
def repo():
    return InMemoryMovieRepository()


@pytest.fixture
def sample_movie():
    return Movie(
        id=1,
        tmdb_id=862,
        title="Toy Story",
        genres="Animation,Comedy,Family",
        cast="Tom Hanks,Tim Allen",
        keywords="jealousy,toy,boy",
        overview="A cowboy doll is profoundly threatened and jealous...",
        avg_rating=4.5,
    )


def test_save_and_get_by_id(repo, sample_movie):
    repo.save(sample_movie)
    fetched = repo.get_by_id(1)
    assert fetched == sample_movie


def test_get_by_id_not_found(repo):
    with pytest.raises(EntityNotFoundError, match="Movie 999 not found"):
        repo.get_by_id(999)


def test_get_all(repo, sample_movie):
    repo.save(sample_movie)
    movies = repo.get_all()
    assert len(movies) == 1
    assert movies[0] == sample_movie


def test_get_by_ids(repo, sample_movie):
    repo.save(sample_movie)
    movies = repo.get_by_ids([1, 2, 3])
    assert len(movies) == 1
    assert movies[0] == sample_movie


def test_filter_by_genre(repo, sample_movie):
    repo.save(sample_movie)
    
    # Matching genre
    comedy_movies = repo.filter_by_genre("comedy")
    assert len(comedy_movies) == 1
    
    # Non-matching genre
    horror_movies = repo.filter_by_genre("horror")
    assert len(horror_movies) == 0
