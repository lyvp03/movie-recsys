from abc import ABC, abstractmethod


class ICFModel(ABC):
    @abstractmethod
    def predict(self, user_id: int, movie_id: int) -> float:
        """Predict the rating a user would give to a movie."""
        pass

    @abstractmethod
    def get_top_n(self, user_id: int, movie_ids: list[int], n: int) -> list[tuple[int, float]]:
        """Return the top-N (movie_id, predicted_score) from the given candidate list."""
        pass
