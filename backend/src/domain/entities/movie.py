from dataclasses import dataclass

from domain.exceptions import InvalidEntityError


@dataclass(frozen=True)
class Movie:
    id: int
    tmdb_id: int
    title: str
    genres: str
    cast: str
    keywords: str
    overview: str
    avg_rating: float

    def __post_init__(self):
        if self.id <= 0:
            raise InvalidEntityError("Movie ID must be greater than 0")
        if not self.title.strip():
            raise InvalidEntityError("Movie title cannot be empty")
        if not (0.0 <= self.avg_rating <= 5.0):
            raise InvalidEntityError("Average rating must be between 0.0 and 5.0")
