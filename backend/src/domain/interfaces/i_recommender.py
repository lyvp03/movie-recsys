from abc import ABC, abstractmethod

from domain.dtos import RecommendationResult


class IRecommender(ABC):
    @abstractmethod
    def recommend(self, reference_id: int, top_k: int) -> list[RecommendationResult]:
        """Return a list of recommendations for the given reference ID."""
        pass
