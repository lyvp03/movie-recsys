from abc import ABC, abstractmethod
from domain.entities.emotion import EmotionVector

class IEmotionRepository(ABC):
    @abstractmethod
    def save(self, movie_id: int, vector: EmotionVector) -> None:
        """Save emotion vector for a movie."""
        pass

    @abstractmethod
    def get_by_movie_id(self, movie_id: int) -> EmotionVector | None:
        """Get emotion vector for a movie, or None if not found."""
        pass

    @abstractmethod
    def get_by_movie_ids(self, movie_ids: list[int]) -> dict[int, EmotionVector]:
        """Get emotion vectors for multiple movies."""
        pass

    @abstractmethod
    def get_all(self) -> dict[int, EmotionVector]:
        """Get all stored emotion vectors. Returns {movie_id: EmotionVector}."""
        pass
