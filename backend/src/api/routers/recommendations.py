from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List
from application.dtos import RecommendationDTO
from application.use_cases.get_tfidf_recommendations import GetTFIDFRecommendations
from application.use_cases.get_embedding_recommendations import GetEmbeddingRecommendations
from application.use_cases.get_collab_recommendations import GetCollabRecommendations
from application.use_cases.get_hybrid_recommendations import GetHybridRecommendations
from domain.exceptions import EntityNotFoundError, DomainError
from api.dependencies import (
    get_tfidf_recommendations_use_case,
    get_embedding_recommendations_use_case,
    get_collab_recommendations_use_case,
    get_hybrid_tfidf_use_case,
    get_hybrid_embedding_use_case,
)

router = APIRouter(prefix="/recommend", tags=["recommendations"])


@router.get("/content-tfidf/{movie_id}", response_model=List[RecommendationDTO])
def get_tfidf_recommendations(
    movie_id: int,
    top_k: int = Query(default=10, ge=1, le=50, description="Number of recommendations to return"),
    use_case: GetTFIDFRecommendations = Depends(get_tfidf_recommendations_use_case),
):
    """
    Get top-K similar movies based on content (TF-IDF features).
    """
    try:
        recommendations = use_case.execute(movie_id, top_k)
        return recommendations
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content-embedding/{movie_id}", response_model=List[RecommendationDTO])
def get_embedding_recommendations(
    movie_id: int,
    top_k: int = Query(default=10, ge=1, le=50, description="Number of recommendations to return"),
    use_case: GetEmbeddingRecommendations = Depends(get_embedding_recommendations_use_case),
):
    """
    Get top-K similar movies based on content (Gemini Embeddings).
    """
    try:
        recommendations = use_case.execute(movie_id, top_k)
        return recommendations
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collab/{user_id}", response_model=List[RecommendationDTO])
def get_collab_recommendations(
    user_id: int,
    top_k: int = Query(default=10, ge=1, le=50, description="Number of recommendations to return"),
    use_case: GetCollabRecommendations = Depends(get_collab_recommendations_use_case),
):
    """
    Get top-K recommendations using Collaborative Filtering (Surprise SVD).
    """
    try:
        recommendations = use_case.execute(user_id, top_k)
        return recommendations
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hybrid-tfidf/{movie_id}", response_model=List[RecommendationDTO])
def get_hybrid_tfidf_recommendations(
    movie_id: int,
    user_id: int = Query(..., description="User ID for collaborative filtering context"),
    top_k: int = Query(default=10, ge=1, le=50, description="Number of recommendations to return"),
    use_case: GetHybridRecommendations = Depends(get_hybrid_tfidf_use_case),
):
    """
    Get top-K recommendations using Hybrid approach (CB with TF-IDF + CF).
    """
    try:
        recommendations = use_case.execute(movie_id, user_id, top_k)
        return recommendations
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hybrid-embedding/{movie_id}", response_model=List[RecommendationDTO])
def get_hybrid_embedding_recommendations(
    movie_id: int,
    user_id: int = Query(..., description="User ID for collaborative filtering context"),
    top_k: int = Query(default=10, ge=1, le=50, description="Number of recommendations to return"),
    use_case: GetHybridRecommendations = Depends(get_hybrid_embedding_use_case),
):
    """
    Get top-K recommendations using Hybrid approach (CB with Gemini Embeddings + CF).
    """
    try:
        recommendations = use_case.execute(movie_id, user_id, top_k)
        return recommendations
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=500, detail=str(e))
