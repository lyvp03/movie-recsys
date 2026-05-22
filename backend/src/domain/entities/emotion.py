import math
from dataclasses import dataclass
from domain.exceptions import ValidationError

@dataclass(frozen=True)
class EmotionVector:
    joy: float = 0.0
    trust: float = 0.0
    fear: float = 0.0
    surprise: float = 0.0
    sadness: float = 0.0
    disgust: float = 0.0
    anger: float = 0.0
    anticipation: float = 0.0

    def __post_init__(self):
        for field_name in ["joy", "trust", "fear", "surprise", "sadness", "disgust", "anger", "anticipation"]:
            val = getattr(self, field_name)
            if val < 0.0:
                raise ValidationError(f"Emotion value '{field_name}' cannot be negative")

    def to_list(self) -> list[float]:
        return [
            self.joy,
            self.trust,
            self.fear,
            self.surprise,
            self.sadness,
            self.disgust,
            self.anger,
            self.anticipation,
        ]

    def to_dict(self) -> dict[str, float]:
        return {
            "joy": self.joy,
            "trust": self.trust,
            "fear": self.fear,
            "surprise": self.surprise,
            "sadness": self.sadness,
            "disgust": self.disgust,
            "anger": self.anger,
            "anticipation": self.anticipation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "EmotionVector":
        return cls(
            joy=data.get("joy", 0.0),
            trust=data.get("trust", 0.0),
            fear=data.get("fear", 0.0),
            surprise=data.get("surprise", 0.0),
            sadness=data.get("sadness", 0.0),
            disgust=data.get("disgust", 0.0),
            anger=data.get("anger", 0.0),
            anticipation=data.get("anticipation", 0.0),
        )

    def cosine_similarity(self, other: "EmotionVector") -> float:
        v1 = self.to_list()
        v2 = other.to_list()
        
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
