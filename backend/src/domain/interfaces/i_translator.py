from abc import ABC, abstractmethod


class ITranslator(ABC):
    """Translate text between languages."""

    @abstractmethod
    def translate_to_english(self, text: str) -> str:
        """Translate any text to English. Returns original if already English."""
        pass
