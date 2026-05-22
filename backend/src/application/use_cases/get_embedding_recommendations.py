import os
from domain.interfaces.i_movie_repo import IMovieRepository
from domain.interfaces.i_vector_store import IVectorStore
from domain.interfaces.i_recommender import IRecommender
from application.dtos import RecommendationDTO

EMBEDDING_COLLECTION = os.getenv("QDRANT_COLLECTION_EMBEDDING", "movies_embedding")


class GetEmbeddingRecommendations(IRecommender):
    def __init__(self, movie_repo: IMovieRepository, vector_store: IVectorStore):
        self._repo = movie_repo
        self._vector_store = vector_store

    def recommend(self, reference_id: int, top_k: int) -> list[RecommendationDTO]:
        return self.execute(reference_id, top_k)

    def execute(self, movie_id: int, top_k: int = 10) -> list[RecommendationDTO]:
        # 1. Ensure movie exists (raises EntityNotFoundError if not)
        movie = self._repo.get_by_id(movie_id)
        
        # 2. Get the vector for this movie from Qdrant
        vector = self._vector_store.get_vector(EMBEDDING_COLLECTION, movie_id)
        
        # 3. Search for nearest neighbors. Ask for top_k + 1 to account for the movie itself.
        search_results = self._vector_store.search(
            collection=EMBEDDING_COLLECTION,
            vector=vector,
            top_k=top_k + 1,
        )
        
        # 4. Filter out the queried movie itself and limit to top_k
        filtered_results = []
        for res in search_results:
            if res.id != movie_id:
                filtered_results.append(res)
            if len(filtered_results) == top_k:
                break
                
        # 5. Enrich with movie details from DB
        if not filtered_results:
            return []
            
        result_ids = [res.id for res in filtered_results]
        movies = self._repo.get_by_ids(result_ids)
        
        # Create a mapping for O(1) lookup
        movie_map = {m.id: m for m in movies}
        
        # 6. Map to DTOs in the order of search results (preserving score ranking)
        dtos = []
        for res in filtered_results:
            m = movie_map.get(res.id)
            if m:
                dtos.append(
                    RecommendationDTO(
                        movie_id=m.id,
                        tmdb_id=m.tmdb_id,
                        title=m.title,
                        genres=m.genres,
                        similarity_score=res.score,
                    )
                )
                
        return dtos
