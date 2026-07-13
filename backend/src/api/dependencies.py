from fastapi import Depends, Request
from sqlmodel import Session

from infrastructure.db.connection import get_session
from infrastructure.db.postgres_movie_repo import PostgresMovieRepository
from infrastructure.db.postgres_rating_repo import PostgresRatingRepository
from infrastructure.vector.qdrant_vector_store import QdrantVectorStore
from application.use_cases.get_tfidf_recommendations import GetTFIDFRecommendations
from application.use_cases.get_embedding_recommendations import GetEmbeddingRecommendations
from application.use_cases.get_collab_recommendations import GetCollabRecommendations
from application.use_cases.get_hybrid_recommendations import GetHybridRecommendations
from application.use_cases.get_emotion_recommendations import GetEmotionRecommendations
from infrastructure.db.postgres_emotion_repo import PostgresEmotionRepository
from infrastructure.ml.nrc_emotion_extractor import NRCEmotionExtractor
from infrastructure.external.ollama_translator import OllamaTranslator


def get_qdrant_client(request: Request):
    """Retrieve the QdrantClient instance from the FastAPI application state."""
    return request.app.state.qdrant_client


def get_cf_model(request: Request):
    """Retrieve the CustomSVDModel instance from the FastAPI application state."""
    return request.app.state.cf_model


def get_movie_repository(session: Session = Depends(get_session)) -> PostgresMovieRepository:
    return PostgresMovieRepository(session)


def get_rating_repository(session: Session = Depends(get_session)) -> PostgresRatingRepository:
    return PostgresRatingRepository(session)


def get_vector_store(qdrant_client=Depends(get_qdrant_client)) -> QdrantVectorStore:
    return QdrantVectorStore(qdrant_client)


def get_tfidf_recommendations_use_case(
    movie_repo: PostgresMovieRepository = Depends(get_movie_repository),
    vector_store: QdrantVectorStore = Depends(get_vector_store),
) -> GetTFIDFRecommendations:
    return GetTFIDFRecommendations(movie_repo, vector_store)


def get_embedding_recommendations_use_case(
    movie_repo: PostgresMovieRepository = Depends(get_movie_repository),
    vector_store: QdrantVectorStore = Depends(get_vector_store),
) -> GetEmbeddingRecommendations:
    return GetEmbeddingRecommendations(movie_repo, vector_store)


def get_collab_recommendations_use_case(
    movie_repo: PostgresMovieRepository = Depends(get_movie_repository),
    rating_repo: PostgresRatingRepository = Depends(get_rating_repository),
    cf_model=Depends(get_cf_model),
) -> GetCollabRecommendations:
    return GetCollabRecommendations(movie_repo, rating_repo, cf_model)


def get_hybrid_tfidf_use_case(
    cb_use_case: GetTFIDFRecommendations = Depends(get_tfidf_recommendations_use_case),
    cf_use_case: GetCollabRecommendations = Depends(get_collab_recommendations_use_case),
    rating_repo: PostgresRatingRepository = Depends(get_rating_repository),
) -> GetHybridRecommendations:
    return GetHybridRecommendations(cb_use_case, cf_use_case, rating_repo)


def get_hybrid_embedding_use_case(
    cb_use_case: GetEmbeddingRecommendations = Depends(get_embedding_recommendations_use_case),
    cf_use_case: GetCollabRecommendations = Depends(get_collab_recommendations_use_case),
    rating_repo: PostgresRatingRepository = Depends(get_rating_repository),
) -> GetHybridRecommendations:
    return GetHybridRecommendations(cb_use_case, cf_use_case, rating_repo)


def get_translator(request: Request) -> OllamaTranslator:
    return request.app.state.translator


def get_emotion_extractor(request: Request) -> NRCEmotionExtractor:
    return request.app.state.emotion_extractor


def get_emotion_repository(session: Session = Depends(get_session)) -> PostgresEmotionRepository:
    return PostgresEmotionRepository(session)


def get_emotion_recommendations_use_case(
    movie_repo: PostgresMovieRepository = Depends(get_movie_repository),
    emotion_repo: PostgresEmotionRepository = Depends(get_emotion_repository),
    translator: OllamaTranslator = Depends(get_translator),
    emotion_extractor: NRCEmotionExtractor = Depends(get_emotion_extractor),
) -> GetEmotionRecommendations:
    return GetEmotionRecommendations(translator, emotion_extractor, emotion_repo, movie_repo)
