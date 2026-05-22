from abc import ABC, abstractmethod


class IEmbeddingEncoder(ABC):
    @abstractmethod
    def encode(self, text: str) -> list[float]:
        """Encode a single text string into a vector."""
        pass

    @abstractmethod
    def encode_batch(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """Encode a list of text strings into a list of vectors."""
        pass
