import logging
import os

from google import genai

from domain.interfaces.i_translator import ITranslator

logger = logging.getLogger(__name__)


class GeminiTranslator(ITranslator):
    """Translate text to English using Google Gemini API with key rotation.

    Rotates through multiple API keys on rate limit (429) errors.
    Falls back to returning original text if all keys exhausted.
    """

    def __init__(self, api_keys: list[str] | None = None, model_name: str = "gemini-2.0-flash"):
        self._api_keys = api_keys or self._load_api_keys()
        if not self._api_keys:
            raise ValueError("No Gemini API keys available for translator")
        self._model_name = model_name
        self._current_key_idx = 0
        self._client = genai.Client(api_key=self._api_keys[0])
        logger.info("GeminiTranslator initialized with %d API keys", len(self._api_keys))

    @staticmethod
    def _load_api_keys() -> list[str]:
        """Load all Gemini API keys from the comma-separated env var."""
        keys_str = os.getenv("GEMINI_API_KEYS", "")
        if not keys_str:
            return []
        return [k.strip() for k in keys_str.split(",") if k.strip()]

    def _rotate_key(self) -> bool:
        """Switch to the next API key. Returns False if all keys exhausted."""
        self._current_key_idx += 1
        if self._current_key_idx >= len(self._api_keys):
            self._current_key_idx = 0  # Wrap around for next request
            return False
        self._client = genai.Client(api_key=self._api_keys[self._current_key_idx])
        logger.info("Rotated to API key %d/%d", self._current_key_idx + 1, len(self._api_keys))
        return True

    def translate_to_english(self, text: str) -> str:
        if not text:
            return text

        prompt = (
            "Translate the following text to English. "
            "If the text is already in English, return it as-is. "
            "Return ONLY the translated text, nothing else — no quotes, no explanation. "
            "If the text is about movies or emotions, preserve the movie/emotion context.\n\n"
            f"{text}"
        )

        # Try each key until one works
        attempts = len(self._api_keys)
        for _ in range(attempts):
            try:
                response = self._client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                )
                translated = response.text.strip()

                if not translated or len(translated) > len(text) * 10:
                    logger.warning("Translation produced suspicious output, using original")
                    return text

                logger.info("Translated '%s' → '%s'", text[:50], translated[:50])
                return translated

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    logger.warning("Key %d/%d rate-limited, rotating...",
                                   self._current_key_idx + 1, len(self._api_keys))
                    if not self._rotate_key():
                        logger.error("All %d API keys exhausted", len(self._api_keys))
                        break
                else:
                    logger.warning("Translation failed: %s", e)
                    return text

        logger.error("Translation failed after trying all keys, using original")
        return text
