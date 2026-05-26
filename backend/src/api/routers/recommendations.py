from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import (
    get_collab_recommendations_use_case,
    get_embedding_recommendations_use_case,
    get_emotion_recommendations_use_case,
    get_hybrid_embedding_use_case,
    get_hybrid_tfidf_use_case,
    get_tfidf_recommendations_use_case,
)
from api.schemas.emotion import EmotionQueryRequest
from application.dtos import EmotionRecommendationDTO, RecommendationDTO
from application.use_cases.get_collab_recommendations import GetCollabRecommendations
from application.use_cases.get_embedding_recommendations import (
    GetEmbeddingRecommendations,
)
from application.use_cases.get_emotion_recommendations import (
    GetEmotionRecommendations,
)
from application.use_cases.get_hybrid_recommendations import GetHybridRecommendations
from application.use_cases.get_tfidf_recommendations import GetTFIDFRecommendations
from domain.exceptions import DomainError, EntityNotFoundError, ValidationError

router = APIRouter(prefix="/recommend", tags=["recommendations"])


@router.get("/content-tfidf/{movie_id}", response_model=List[RecommendationDTO])
def get_tfidf_recommendations(
    movie_id: int,
    top_k: int = Query(
        default=10, ge=1, le=50, description="Number of recommendations to return"
    ),
    use_case: GetTFIDFRecommendations = Depends(
        get_tfidf_recommendations_use_case
    ),
):
    """Get top-K similar movies based on content (TF-IDF features)."""
    try:
        return use_case.execute(movie_id, top_k)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content-embedding/{movie_id}", response_model=List[RecommendationDTO])
def get_embedding_recommendations(
    movie_id: int,
    top_k: int = Query(
        default=10, ge=1, le=50, description="Number of recommendations to return"
    ),
    use_case: GetEmbeddingRecommendations = Depends(
        get_embedding_recommendations_use_case
    ),
):
    """Get top-K similar movies based on content (Semantic Embeddings)."""
    try:
        return use_case.execute(movie_id, top_k)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collab/{user_id}", response_model=List[RecommendationDTO])
def get_collab_recommendations(
    user_id: int,
    top_k: int = Query(
        default=10, ge=1, le=50, description="Number of recommendations to return"
    ),
    use_case: GetCollabRecommendations = Depends(
        get_collab_recommendations_use_case
    ),
):
    """Get top-K recommendations using Collaborative Filtering (SVD)."""
    try:
        return use_case.execute(user_id, top_k)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hybrid-tfidf/{movie_id}", response_model=List[RecommendationDTO])
def get_hybrid_tfidf_recommendations(
    movie_id: int,
    user_id: int = Query(
        ..., description="User ID for collaborative filtering context"
    ),
    top_k: int = Query(
        default=10, ge=1, le=50, description="Number of recommendations to return"
    ),
    use_case: GetHybridRecommendations = Depends(get_hybrid_tfidf_use_case),
):
    """Get top-K recommendations using Hybrid approach (CB with TF-IDF + CF)."""
    try:
        return use_case.execute(movie_id, user_id, top_k)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hybrid-embedding/{movie_id}", response_model=List[RecommendationDTO])
def get_hybrid_embedding_recommendations(
    movie_id: int,
    user_id: int = Query(
        ..., description="User ID for collaborative filtering context"
    ),
    top_k: int = Query(
        default=10, ge=1, le=50, description="Number of recommendations to return"
    ),
    use_case: GetHybridRecommendations = Depends(get_hybrid_embedding_use_case),
):
    """Get top-K recommendations using Hybrid approach (CB with Embeddings + CF)."""
    try:
        return use_case.execute(movie_id, user_id, top_k)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emotion", response_model=List[EmotionRecommendationDTO])
def get_emotion_recommendations(
    request: EmotionQueryRequest,
    use_case: GetEmotionRecommendations = Depends(
        get_emotion_recommendations_use_case
    ),
):
    """Get top-K recommendations based on natural language emotional query."""
    try:
        return use_case.execute(request.query, request.top_k)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=500, detail=str(e))
