from application.dtos import EmotionRecommendationDTO
from domain.exceptions import ValidationError, DomainError
from domain.interfaces.i_embedding_encoder import IEmbeddingEncoder
from domain.interfaces.i_emotion_repo import IEmotionRepository
from domain.interfaces.i_movie_repo import IMovieRepository
from domain.interfaces.i_vector_store import IVectorStore

DEFAULT_EMOTION_COLLECTION = "movies_emotion"
DEFAULT_EMBEDDING_COLLECTION = "movies_embedding"

MIN_QUERY_LENGTH = 3


class GetEmotionRecommendations:
    def __init__(
        self,
        embedding_encoder: IEmbeddingEncoder,
        vector_store: IVectorStore,
        movie_repo: IMovieRepository,
        emotion_repo: IEmotionRepository,
        emotion_collection: str = DEFAULT_EMOTION_COLLECTION,
        embedding_collection: str = DEFAULT_EMBEDDING_COLLECTION,
    ):
        self._encoder = embedding_encoder
        self._vector_store = vector_store
        self._movie_repo = movie_repo
        self._emotion_repo = emotion_repo
        self._emotion_collection = emotion_collection
        self._embedding_collection = embedding_collection

    def execute(self, query: str, top_k: int = 10) -> list[EmotionRecommendationDTO]:
        if not query or len(query.strip()) < MIN_QUERY_LENGTH:
            raise ValidationError("Query must be at least 3 characters long")

        if top_k <= 0:
            raise ValidationError("top_k must be greater than 0")

        # 1. Encode query text
        try:
            query_vector = self._encoder.encode(query)
        except Exception as e:
            raise DomainError(f"Failed to encode query: {e}")

        # 2. Search Qdrant "movies_emotion"
        try:
            emotion_results = self._vector_store.search(
                collection=self._emotion_collection,
                vector=query_vector,
                top_k=top_k,
            )
        except Exception:
            # If collection doesn't exist or fails, treat as 0 results
            emotion_results = []

        results_dict: dict[int, dict] = {}
        for res in emotion_results:
            results_dict[res.id] = {"score": res.score, "source": "emotion"}

        # 3. If results < top_k, fallback to "movies_embedding"
        if len(results_dict) < top_k:
            needed = top_k - len(results_dict)
            try:
                fallback_results = self._vector_store.search(
                    collection=self._embedding_collection,
                    vector=query_vector,
                    top_k=top_k * 2,
                )

                for res in fallback_results:
                    if res.id not in results_dict:
                        results_dict[res.id] = {
                            "score": res.score,
                            "source": "embedding",
                        }
                        needed -= 1
                    if needed <= 0:
                        break
            except Exception:
                pass  # Fallback failed, continue with whatever we have

        if not results_dict:
            return []

        # 4. Enrich with movie details
        result_ids = list(results_dict.keys())
        movies = self._movie_repo.get_by_ids(result_ids)
        movie_map = {m.id: m for m in movies}

        # 5. Attach emotion metadata
        emotion_vectors = self._emotion_repo.get_by_movie_ids(result_ids)

        # 6. Build final DTOs, sorted by score descending
        sorted_results = sorted(
            results_dict.items(), key=lambda x: x[1]["score"], reverse=True
        )

        dtos = []
        for mid, info in sorted_results[:top_k]:
            m = movie_map.get(mid)
            if m:
                ev = emotion_vectors.get(mid)
                emotion_tags = ev.to_dict() if ev else None

                dtos.append(
                    EmotionRecommendationDTO(
                        movie_id=m.id,
                        tmdb_id=m.tmdb_id,
                        title=m.title,
                        genres=m.genres,
                        similarity_score=info["score"],
                        emotion_tags=emotion_tags,
                    )
                )

        return dtos
