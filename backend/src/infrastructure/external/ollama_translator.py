import logging
import os

import requests

from domain.interfaces.i_translator import ITranslator

logger = logging.getLogger(__name__)

OLLAMA_CLOUD_URL = "https://ollama.com/api/chat"

# Map common movie/genre words to emotion-rich synonyms for NRC lexicon
_EMOTION_EXPANSION: dict[str, str] = {
    "comedy": "hilarious joyful amusing",
    "horror": "horror terrified dread",
    "romance": "romantic love tender passionate",
    "romantic": "romantic love tender passionate",
    "drama": "emotional poignant sorrow",
    "thriller": "suspense danger tension fear",
    "action": "excitement thrill adventure heroic",
    "family": "love warmth togetherness joyful",
    "animation": "wonder magical playful joyful",
    "sci-fi": "wonder mysterious alien futuristic",
    "fantasy": "wonder magical enchanted mystical",
    "war": "battle sacrifice courage sorrow",
    "musical": "joyful melodious harmony celebration",
    "documentary": "truth revelation enlightenment",
    "mystery": "mystery suspicion intrigue curious",
    "western": "adventure frontier rugged heroic",
    "sad": "sadness sorrow grief melancholy",
    "scary": "fear terror dread frightening",
    "funny": "hilarious amusing laughter joy",
    "gentle": "tender calm peaceful serene",
    "light": "cheerful bright carefree playful",
    "dark": "gloomy despair sinister menacing",
    "warm": "affection tender comfort love",
    "sweet": "delightful charming lovely adorable",
    "intense": "passionate fierce powerful gripping",
    "cute": "adorable charming delightful lovely",
    "emotional": "poignant touching heartfelt sorrow",
    "exciting": "thrill exhilarating adventure",
    "boring": "tedious dull monotony apathy",
    "beautiful": "beautiful gorgeous stunning magnificent",
    "heartwarming": "tender love joy gratitude",
    "movie": "",
    "film": "",
    "movies": "",
    "films": "",
}


class OllamaTranslator(ITranslator):
    """Translate text to English using Ollama Cloud API (nemotron-3-super).

    Uses Ollama's native /api/chat endpoint at https://ollama.com/api/chat.
    Also expands genre/movie keywords into emotion-rich synonyms
    so NRC lexicon can extract meaningful signals.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "nemotron-3-super:cloud",
    ):
        self._api_key = api_key or os.getenv("OLLAMA_API_KEY", "")
        if not self._api_key:
            raise ValueError("OLLAMA_API_KEY not set")
        self._model = model

    def translate_to_english(self, text: str) -> str:
        if not text:
            return text

        try:
            payload = {
                "model": self._model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a translator. Translate the user's text to English. "
                            "Return ONLY the translated text, nothing else. "
                            "If already English, return as-is."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                "stream": False,
            }

            response = requests.post(
                OLLAMA_CLOUD_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )

            if response.status_code != 200:
                logger.warning(
                    "Ollama API returned %d: %s", response.status_code, response.text[:200]
                )
                return text

            data = response.json()
            translated = data["message"]["content"].strip()

            if not translated or len(translated) > len(text) * 10:
                logger.warning("Translation suspicious, using original")
                return text

            logger.info("Translated '%s' → '%s'", text[:50], translated[:50])

            # Expand genre/movie words into emotion-rich synonyms
            expanded = self._expand_emotion_keywords(translated)
            if expanded != translated:
                logger.info("Expanded → '%s'", expanded[:80])

            return expanded

        except Exception as e:
            logger.warning("Translation failed: %s", e)
            return text

    @staticmethod
    def _expand_emotion_keywords(text: str) -> str:
        """Replace genre/movie words with emotion-rich synonyms for NRC."""
        words = text.lower().split()
        expanded_parts = []
        for word in words:
            clean = word.strip(".,!?;:'\"")
            if clean in _EMOTION_EXPANSION:
                replacement = _EMOTION_EXPANSION[clean]
                if replacement:
                    expanded_parts.append(replacement)
            else:
                expanded_parts.append(word)
        return " ".join(expanded_parts)
