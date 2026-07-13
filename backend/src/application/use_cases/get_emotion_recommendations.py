"""Emotion-based movie recommendations.

Flow:
  1. Translate query to English (if not already)
  2. NRC extract emotion vector from translated query (8 dims)
  3. Load all movie emotion vectors from Postgres
  4. Cosine similarity rank → top-k
  5. Enrich with movie metadata
"""

import logging

from application.dtos import EmotionRecommendationDTO
from domain.exceptions import DomainError, ValidationError
from domain.interfaces.i_emotion_extractor import IEmotionExtractor
from domain.interfaces.i_emotion_repo import IEmotionRepository
from domain.interfaces.i_movie_repo import IMovieRepository
from domain.interfaces.i_translator import ITranslator

logger = logging.getLogger(__name__)

MIN_QUERY_LENGTH = 3


class GetEmotionRecommendations:
    def __init__(
        self,
        translator: ITranslator,
        emotion_extractor: IEmotionExtractor,
        emotion_repo: IEmotionRepository,
        movie_repo: IMovieRepository,
    ):
        self._translator = translator
        self._extractor = emotion_extractor
        self._emotion_repo = emotion_repo
        self._movie_repo = movie_repo

    def execute(self, query: str, top_k: int = 10) -> list[EmotionRecommendationDTO]:
        if not query or len(query.strip()) < MIN_QUERY_LENGTH:
            raise ValidationError("Query must be at least 3 characters long")

        if top_k <= 0:
            raise ValidationError("top_k must be greater than 0")

        # 1. Translate query to English (NRC lexicon is English-only)
        try:
            english_query = self._translator.translate_to_english(query)
        except Exception as e:
            raise DomainError(f"Failed to translate query: {e}")

        logger.info("Query: '%s' → English: '%s'", query, english_query)

        # 2. Extract emotion vector from the English query
        query_emotion = self._extractor.extract(english_query)
        query_list = query_emotion.to_list()

        # Check if NRC produced any meaningful signal
        if sum(query_list) == 0:
            logger.warning("NRC found no emotion in query '%s', using fallback", english_query)
            # If NRC can't extract anything, we can still try —
            # but results won't be great. Return empty or fallback.
            return []

        # 3. Load all stored movie emotion vectors
        all_emotions = self._emotion_repo.get_all()
        if not all_emotions:
            return []

        # 4. Compute cosine similarity between query emotion and each movie's emotion
        scored: list[tuple[int, float]] = []
        for movie_id, movie_emotion in all_emotions.items():
            score = query_emotion.cosine_similarity(movie_emotion)
            scored.append((movie_id, score))

        # Sort by score descending. To break ties, we'll need avg_rating, so fetch movies first.
        # But fetching all movies is slow. So we fetch top N initially, or we just sort by score.
        # Wait, let's fetch all top scoring movies (say, anything with score > 0)
        # to break ties by rating.
        # Alternatively, we just get top 100 by score, then fetch their ratings, and re-sort.
        scored.sort(key=lambda x: x[1], reverse=True)
        top_100_ids = [mid for mid, _ in scored[:100]]
        
        movies = self._movie_repo.get_by_ids(top_100_ids)
        movie_map = {m.id: m for m in movies}
        
        # Re-sort top 100 by (score, rating)
        top_100_scored = [(mid, score) for mid, score in scored[:100] if mid in movie_map]
        top_100_scored.sort(key=lambda x: (x[1], movie_map[x[0]].avg_rating), reverse=True)
        
        top_results = top_100_scored[:top_k]

        if not top_results:
            return []

        # 5. Enrich with movie details
        top_movie_ids = [mid for mid, _ in top_results]

        # 6. Get emotion vectors for the top results (for response metadata)
        top_emotions = {mid: all_emotions[mid] for mid in top_movie_ids if mid in all_emotions}

        # 7. Build DTOs
        dtos = []
        for mid, score in top_results:
            m = movie_map.get(mid)
            if m:
                ev = top_emotions.get(mid)
                dtos.append(
                    EmotionRecommendationDTO(
                        movie_id=m.id,
                        tmdb_id=m.tmdb_id,
                        title=m.title,
                        genres=m.genres,
                        similarity_score=round(score, 6),
                        emotion_tags=ev.to_dict() if ev else None,
                    )
                )

        return dtos
