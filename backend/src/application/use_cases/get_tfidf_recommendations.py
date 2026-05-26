from domain.interfaces.i_movie_repo import IMovieRepository
from domain.interfaces.i_vector_store import IVectorStore
from application.use_cases.content_based_recommendations import (
    ContentBasedRecommendations,
)

DEFAULT_TFIDF_COLLECTION = "movies_tfidf"


class GetTFIDFRecommendations(ContentBasedRecommendations):
    """Content-based recommendations using TF-IDF vectors."""

    def __init__(
        self,
        movie_repo: IMovieRepository,
        vector_store: IVectorStore,
        collection_name: str = DEFAULT_TFIDF_COLLECTION,
    ):
        super().__init__(movie_repo, vector_store, collection_name)
