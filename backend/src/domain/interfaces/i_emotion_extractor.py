from abc import ABC, abstractmethod
from domain.entities.emotion import EmotionVector

class IEmotionExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> EmotionVector:
        """Extract emotion scores from a text string."""
        pass
