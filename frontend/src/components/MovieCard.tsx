import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import StarRating from './StarRating';
import EmotionTag from './EmotionTag';
import { getMovieDetail } from '../services/api';

interface MovieCardProps {
  movieId: number;
  tmdbId: number;
  title: string;
  genres: string;
  avgRating?: number;
  similarityScore?: number;
  emotionTags?: Record<string, number> | null;
  posterUrl?: string | null;
}

export default function MovieCard({
  movieId,
  tmdbId,
  title,
  genres,
  avgRating,
  similarityScore,
  emotionTags,
  posterUrl,
}: MovieCardProps) {
  const navigate = useNavigate();
  const [actualPosterUrl, setActualPosterUrl] = useState<string | null>(posterUrl || null);
  const genreList = genres ? genres.split(',').map((g) => g.trim()).filter(Boolean).slice(0, 3) : [];

  useEffect(() => {
    // If we don't have a valid poster URL yet, fetch it from our backend
    // which acts as a proxy to TMDB API.
    if (!actualPosterUrl || !actualPosterUrl.includes('.jpg')) {
      getMovieDetail(movieId).then(detail => {
        if (detail.poster_url) {
          setActualPosterUrl(detail.poster_url);
        }
      }).catch(console.error);
    }
  }, [movieId, actualPosterUrl]);

  return (
    <div
      onClick={() => navigate(`/movie/${movieId}`)}
      className="glass-card-hover cursor-pointer overflow-hidden group"
    >
      {/* Poster */}
      <div className="aspect-[2/3] bg-surface-800 relative overflow-hidden">
        {actualPosterUrl ? (
          <img
            src={actualPosterUrl}
            alt={title}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
            loading="lazy"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl text-gray-600">
            🎬
          </div>
        )}

        {/* Score overlay */}
        {similarityScore !== undefined && (
          <div className="absolute top-2 right-2 bg-primary-600/90 backdrop-blur-sm text-white text-xs font-bold px-2 py-1 rounded-lg">
            {(similarityScore * 100).toFixed(0)}% match
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-4 space-y-2">
        <h3 className="font-semibold text-sm text-gray-100 line-clamp-2 group-hover:text-primary-300 transition-colors">
          {title}
        </h3>

        {avgRating !== undefined && avgRating > 0 && <StarRating rating={avgRating} />}

        {/* Genres */}
        <div className="flex flex-wrap gap-1">
          {genreList.map((g) => (
            <span key={g} className="genre-badge text-[10px]">{g}</span>
          ))}
        </div>

        {/* Emotion tags */}
        {emotionTags && (
          <div className="flex flex-wrap gap-1 pt-1">
            {Object.entries(emotionTags)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 3)
              .map(([emotion, score]) => (
                <EmotionTag key={emotion} emotion={emotion} score={score} />
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
