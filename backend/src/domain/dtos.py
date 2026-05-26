from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendationResult:
    """Domain-level recommendation result."""

    movie_id: int
    tmdb_id: int
    title: str
    genres: str
    similarity_score: float


@dataclass(frozen=True)
class EmotionRecommendationResult(RecommendationResult):
    """Domain-level emotion recommendation result with emotion metadata."""

    emotion_tags: dict[str, float] | None = None
