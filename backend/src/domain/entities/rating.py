from dataclasses import dataclass
from datetime import datetime

from domain.exceptions import InvalidEntityError


@dataclass(frozen=True)
class Rating:
    id: int
    user_id: int
    movie_id: int
    rating: float
    rated_at: datetime

    def __post_init__(self):
        if not (0.5 <= self.rating <= 5.0):
            raise InvalidEntityError("Rating must be between 0.5 and 5.0")
