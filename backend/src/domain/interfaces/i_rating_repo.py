from abc import ABC, abstractmethod

from domain.entities.rating import Rating


class IRatingRepository(ABC):
    @abstractmethod
    def get_by_user(self, user_id: int) -> list[Rating]:
        """Get all ratings by a specific user."""
        pass

    @abstractmethod
    def get_all(self) -> list[Rating]:
        """Get all ratings (for training)."""
        pass

    @abstractmethod
    def get_user_rated_movie_ids(self, user_id: int) -> set[int]:
        """Return a set of movie IDs that the user has already rated."""
        pass

    @abstractmethod
    def count_by_user(self, user_id: int) -> int:
        """Count the number of ratings for cold start strategy."""
        pass
