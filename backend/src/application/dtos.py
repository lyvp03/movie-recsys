"""Application-layer DTOs.

Re-exports domain DTOs for backward compatibility.
Application-specific DTO extensions can be added here.
"""

from domain.dtos import EmotionRecommendationResult as EmotionRecommendationDTO
from domain.dtos import RecommendationResult as RecommendationDTO

__all__ = ["RecommendationDTO", "EmotionRecommendationDTO"]
