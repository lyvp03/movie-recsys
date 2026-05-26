from abc import ABC, abstractmethod

from domain.entities.movie import Movie


class IMovieRepository(ABC):
    @abstractmethod
    def get_by_id(self, movie_id: int) -> Movie:
        pass

    @abstractmethod
    def get_all(self) -> list[Movie]:
        pass

    @abstractmethod
    def get_all_ids(self) -> list[int]:
        """Return all movie IDs without loading full entities."""
        pass

    @abstractmethod
    def get_by_ids(self, movie_ids: list[int]) -> list[Movie]:
        pass

    @abstractmethod
    def filter_by_genre(self, genre: str) -> list[Movie]:
        pass
