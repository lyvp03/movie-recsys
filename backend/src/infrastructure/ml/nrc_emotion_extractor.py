import re
from pathlib import Path

from domain.entities.emotion import EmotionVector
from domain.interfaces.i_emotion_extractor import IEmotionExtractor

class NRCEmotionExtractor(IEmotionExtractor):
    def __init__(self, lexicon_path: str = "data/raw/NRC-Emotion-Lexicon.txt"):
        self.lexicon_path = Path(lexicon_path)
        # map: word -> dict of emotions { "anger": 1, "joy": 0, ... }
        self._lexicon: dict[str, dict[str, int]] = {}
        self._load_lexicon()

    def _load_lexicon(self):
        if not self.lexicon_path.exists():
            # If not exists, initialize empty. The script can download it later.
            return
            
        with open(self.lexicon_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) == 3:
                    word, emotion, assoc = parts
                    word = word.lower()
                    
                    if word not in self._lexicon:
                        self._lexicon[word] = {}
                        
                    # assoc is "0" or "1"
                    try:
                        self._lexicon[word][emotion] = int(assoc)
                    except ValueError:
                        pass

    def extract(self, text: str) -> EmotionVector:
        if not text:
            return EmotionVector()

        # Tokenize (lowercase, extract words)
        words = re.findall(r"\b\w+\b", text.lower())
        
        counts = {
            "joy": 0, "trust": 0, "fear": 0, "surprise": 0,
            "sadness": 0, "disgust": 0, "anger": 0, "anticipation": 0
        }
        
        total_hits = 0
        for word in words:
            if word in self._lexicon:
                emotions = self._lexicon[word]
                for emo, assoc in emotions.items():
                    if emo in counts and assoc == 1:
                        counts[emo] += 1
                        total_hits += 1

        if total_hits == 0:
            return EmotionVector()
            
        # Normalize
        normalized = {k: v / total_hits for k, v in counts.items()}
        return EmotionVector.from_dict(normalized)
