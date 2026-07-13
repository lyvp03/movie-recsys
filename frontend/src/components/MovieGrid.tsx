import MovieCard from './MovieCard';
import type { RecommendationDTO, EmotionRecommendationDTO } from '../types/movie';

interface MovieGridProps {
  movies: (RecommendationDTO | EmotionRecommendationDTO)[];
  loading?: boolean;
  emptyMessage?: string;
}

export default function MovieGrid({ movies, loading, emptyMessage = 'No movies found' }: MovieGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="glass-card overflow-hidden animate-pulse">
            <div className="aspect-[2/3] bg-surface-700" />
            <div className="p-4 space-y-2">
              <div className="h-4 bg-surface-700 rounded w-3/4" />
              <div className="h-3 bg-surface-700 rounded w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (movies.length === 0) {
    return (
      <div className="text-center py-20 text-gray-500">
        <p className="text-4xl mb-4">🎞️</p>
        <p className="text-lg">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {movies.map((m) => (
        <MovieCard
          key={m.movie_id}
          movieId={m.movie_id}
          tmdbId={m.tmdb_id}
          title={m.title}
          genres={m.genres}
          similarityScore={m.similarity_score}
          emotionTags={'emotion_tags' in m ? m.emotion_tags : undefined}
        />
      ))}
    </div>
  );
}
