import pytest

from domain.entities.movie import Movie
from domain.exceptions import InvalidEntityError


def test_movie_creation_success():
    movie = Movie(
        id=1,
        tmdb_id=862,
        title="Toy Story",
        genres="Animation,Comedy,Family",
        cast="Tom Hanks,Tim Allen",
        keywords="jealousy,toy,boy",
        overview="A cowboy doll is profoundly threatened and jealous when a new spaceman figure supplants him as top toy in a boy's room.",
        avg_rating=4.5,
    )
    assert movie.id == 1
    assert movie.title == "Toy Story"
    assert movie.avg_rating == 4.5


def test_movie_creation_invalid_id():
    with pytest.raises(InvalidEntityError, match="Movie ID must be greater than 0"):
        Movie(
            id=0,
            tmdb_id=862,
            title="Toy Story",
            genres="",
            cast="",
            keywords="",
            overview="",
            avg_rating=4.0,
        )


def test_movie_creation_empty_title():
    with pytest.raises(InvalidEntityError, match="Movie title cannot be empty"):
        Movie(
            id=1,
            tmdb_id=862,
            title="",
            genres="",
            cast="",
            keywords="",
            overview="",
            avg_rating=4.0,
        )


def test_movie_creation_invalid_rating():
    with pytest.raises(InvalidEntityError, match="Average rating must be between 0.0 and 5.0"):
        Movie(
            id=1,
            tmdb_id=862,
            title="Toy Story",
            genres="",
            cast="",
            keywords="",
            overview="",
            avg_rating=5.5,
        )

    with pytest.raises(InvalidEntityError, match="Average rating must be between 0.0 and 5.0"):
        Movie(
            id=1,
            tmdb_id=862,
            title="Toy Story",
            genres="",
            cast="",
            keywords="",
            overview="",
            avg_rating=-1.0,
        )
