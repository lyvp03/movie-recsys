from application.dtos import RecommendationDTO
from domain.exceptions import DomainError, EntityNotFoundError
from domain.interfaces.i_recommender import IRecommender
from domain.interfaces.i_rating_repo import IRatingRepository
from application.use_cases.get_collab_recommendations import GetCollabRecommendations


class GetHybridRecommendations:
    def __init__(
        self,
        cb_recommender: IRecommender,
        cf_recommender: GetCollabRecommendations,
        rating_repo: IRatingRepository,
    ):
        """
        :param cb_recommender: Any content-based recommender (TF-IDF or Embedding)
        :param cf_recommender: The collaborative filtering recommender use case
        :param rating_repo: The rating repository for checking user history to determine weights
        """
        self._cb_recommender = cb_recommender
        self._cf_recommender = cf_recommender
        self._rating_repo = rating_repo

    def execute(self, movie_id: int, user_id: int, top_k: int = 10) -> list[RecommendationDTO]:
        if top_k <= 0:
            raise DomainError("top_k must be greater than 0")

        # 1. Determine weights based on user's rating count (Cold Start Strategy)
        count = self._rating_repo.count_by_user(user_id)
        if count < 5:
            w_cb, w_cf = 1.0, 0.0
        elif count <= 20:
            w_cb, w_cf = 0.7, 0.3
        else:
            w_cb, w_cf = 0.3, 0.7

        # 2. Get CB results (fetch 2*top_k to have enough candidates after merging)
        try:
            cb_results = self._cb_recommender.recommend(movie_id, top_k * 2)
        except EntityNotFoundError as e:
            # Re-raise so the API can return 404
            raise e
        except Exception as e:
            raise DomainError(f"CB recommendation failed: {e}")

        # 3. Get CF results (if weight > 0)
        cf_results = []
        if w_cf > 0:
            try:
                cf_results = self._cf_recommender.execute(user_id, top_k * 2)
            except Exception as e:
                # If CF fails (e.g. no pre-trained model), fallback to pure CB
                w_cb, w_cf = 1.0, 0.0

        # 4. Weighted merge + dedup
        score_map = {}
        movie_details = {}

        # Merge CB
        for r in cb_results:
            score_map[r.movie_id] = score_map.get(r.movie_id, 0.0) + w_cb * r.similarity_score
            movie_details[r.movie_id] = r

        # Merge CF (normalize score from 1-5 to 0-1 scale)
        for r in cf_results:
            normalized_cf_score = r.similarity_score / 5.0
            score_map[r.movie_id] = score_map.get(r.movie_id, 0.0) + w_cf * normalized_cf_score
            if r.movie_id not in movie_details:
                movie_details[r.movie_id] = r

        # 5. Sort by combined score and return top_k
        sorted_items = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for mid, final_score in sorted_items[:top_k]:
            original_dto = movie_details[mid]
            # Create a new DTO with the hybrid score
            hybrid_dto = RecommendationDTO(
                movie_id=original_dto.movie_id,
                tmdb_id=original_dto.tmdb_id,
                title=original_dto.title,
                genres=original_dto.genres,
                similarity_score=final_score,
            )
            recommendations.append(hybrid_dto)

        return recommendations
