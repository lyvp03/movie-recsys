import logging

from deep_translator import GoogleTranslator

from domain.interfaces.i_translator import ITranslator

logger = logging.getLogger(__name__)

# Map common movie/genre words to emotion-rich synonyms for NRC lexicon
_EMOTION_EXPANSION: dict[str, str] = {
    # Genre words → emotion-rich equivalents
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
    # Common adjectives not in NRC
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


class DeepTranslator(ITranslator):
    """Translate text to English using Google Translate (free, no API key).

    Also expands genre/movie keywords into emotion-rich synonyms
    so NRC lexicon can extract meaningful signals.
    """

    def __init__(self, source: str = "auto", target: str = "en"):
        self._source = source
        self._target = target

    def translate_to_english(self, text: str) -> str:
        if not text:
            return text

        try:
            translated = GoogleTranslator(
                source=self._source, target=self._target
            ).translate(text)

            if not translated:
                logger.warning("Translation returned empty, using original")
                return text

            logger.info("Translated '%s' → '%s'", text[:50], translated[:50])

            # Expand genre/movie words into emotion-rich synonyms
            expanded = self._expand_emotion_keywords(translated)
            if expanded != translated:
                logger.info("Expanded → '%s'", expanded[:80])

            return expanded

        except Exception as e:
            logger.warning("Translation failed, using original: %s", e)
            return text

    @staticmethod
    def _expand_emotion_keywords(text: str) -> str:
        """Replace genre/movie words with emotion-rich synonyms for NRC."""
        words = text.lower().split()
        expanded_parts = []
        for word in words:
            # Strip punctuation for lookup
            clean = word.strip(".,!?;:'\"")
            if clean in _EMOTION_EXPANSION:
                replacement = _EMOTION_EXPANSION[clean]
                if replacement:  # Skip empty replacements (e.g., "movie")
                    expanded_parts.append(replacement)
            else:
                expanded_parts.append(word)
        return " ".join(expanded_parts)
