from dataclasses import dataclass


@dataclass
class RecommendationDTO:
    movie_id: int
    tmdb_id: int
    title: str
    genres: str
    similarity_score: float

@dataclass
class EmotionRecommendationDTO(RecommendationDTO):
    emotion_tags: dict[str, float] | None = None
