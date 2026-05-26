from domain.interfaces.i_movie_repo import IMovieRepository
from domain.interfaces.i_vector_store import IVectorStore
from application.use_cases.content_based_recommendations import (
    ContentBasedRecommendations,
)

DEFAULT_EMBEDDING_COLLECTION = "movies_embedding"


class GetEmbeddingRecommendations(ContentBasedRecommendations):
    """Content-based recommendations using dense semantic embeddings."""

    def __init__(
        self,
        movie_repo: IMovieRepository,
        vector_store: IVectorStore,
        collection_name: str = DEFAULT_EMBEDDING_COLLECTION,
    ):
        super().__init__(movie_repo, vector_store, collection_name)
