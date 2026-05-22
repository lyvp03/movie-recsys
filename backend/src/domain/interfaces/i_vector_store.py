from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    id: int
    score: float
    payload: dict


class IVectorStore(ABC):
    @abstractmethod
    def upsert(self, collection: str, id: int, vector: list[float], payload: dict) -> None:
        pass

    @abstractmethod
    def search(self, collection: str, vector: list[float], top_k: int) -> list[SearchResult]:
        pass

    @abstractmethod
    def delete(self, collection: str, id: int) -> None:
        pass

    @abstractmethod
    def get_vector(self, collection: str, id: int) -> list[float]:
        """Retrieve the vector representation of an item from the store."""
        pass
