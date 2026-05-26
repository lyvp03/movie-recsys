from application.dtos import RecommendationDTO
from domain.exceptions import EntityNotFoundError, DomainError
from domain.interfaces.i_cf_model import ICFModel
from domain.interfaces.i_movie_repo import IMovieRepository
from domain.interfaces.i_rating_repo import IRatingRepository


class GetCollabRecommendations:
    def __init__(
        self,
        movie_repo: IMovieRepository,
        rating_repo: IRatingRepository,
        cf_model: ICFModel,
    ):
        self._movie_repo = movie_repo
        self._rating_repo = rating_repo
        self._cf_model = cf_model

    def execute(self, user_id: int, top_k: int = 10) -> list[RecommendationDTO]:
        if top_k <= 0:
            raise DomainError("top_k must be greater than 0")

        # 1. Get movies the user has already rated
        rated_ids = self._rating_repo.get_user_rated_movie_ids(user_id)

        # 2. Get all movie IDs as candidates (exclude already rated)
        # Uses get_all_ids() to avoid loading full entities into memory
        all_movie_ids = self._movie_repo.get_all_ids()
        candidates = [mid for mid in all_movie_ids if mid not in rated_ids]
        
        if not candidates:
            return []

        # 3. Predict scores and get top-K candidates
        try:
            top_n = self._cf_model.get_top_n(user_id, candidates, top_k)
        except Exception as e:
            raise DomainError(f"Failed to get predictions: {e}")

        # 4. Enrich only the top-K results with full movie details
        top_movie_ids = [mid for mid, _ in top_n]
        movies = self._movie_repo.get_by_ids(top_movie_ids)
        movie_dict = {m.id: m for m in movies}
        
        recommendations = []
        for movie_id, score in top_n:
            movie = movie_dict.get(movie_id)
            if movie:
                dto = RecommendationDTO(
                    movie_id=movie.id,
                    tmdb_id=movie.tmdb_id,
                    title=movie.title,
                    genres=movie.genres,
                    similarity_score=score,
                )
                recommendations.append(dto)

        return recommendations
