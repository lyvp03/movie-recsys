import re

from domain.entities.emotion import EmotionVector
from domain.interfaces.i_emotion_extractor import IEmotionExtractor


# The 8 Plutchik emotions we track
_EMOTION_NAMES = frozenset(
    ["joy", "trust", "fear", "surprise", "sadness", "disgust", "anger", "anticipation"]
)


class NRCEmotionExtractor(IEmotionExtractor):
    """Extract emotion scores from text using the NRC Emotion Lexicon.

    Uses the bundled NRCLex package lexicon (14k words → 8 Plutchik emotions).
    """

    def __init__(self) -> None:
        # NRCLex stores its lexicon as a class-level dict.
        # We extract it once at init time to avoid re-processing per call.
        from nrclex import NRCLex

        # NRCLex requires a text argument; we pass a dummy to access the lexicon.
        # Note: __lexicon__ is the only way to access the raw word→emotion mapping.
        dummy = NRCLex("dummy")
        self._lexicon: dict[str, list[str]] = dummy.__lexicon__

    def extract(self, text: str) -> EmotionVector:
        if not text:
            return EmotionVector()

        # Tokenize (lowercase, extract words)
        words = re.findall(r"\b\w+\b", text.lower())

        counts: dict[str, int] = {emo: 0 for emo in _EMOTION_NAMES}
        total_hits = 0

        for word in words:
            emotions = self._lexicon.get(word, [])
            for emo in emotions:
                if emo in counts:
                    counts[emo] += 1
                    total_hits += 1

        if total_hits == 0:
            return EmotionVector()

        # Normalize so all values sum to 1.0
        normalized = {k: v / total_hits for k, v in counts.items()}
        return EmotionVector.from_dict(normalized)
