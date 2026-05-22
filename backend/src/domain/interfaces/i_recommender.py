from abc import ABC, abstractmethod

from application.dtos import RecommendationDTO


class IRecommender(ABC):
    @abstractmethod
    def recommend(self, reference_id: int, top_k: int) -> list[RecommendationDTO]:
        """Return a list of recommendations for the given reference ID."""
        pass
