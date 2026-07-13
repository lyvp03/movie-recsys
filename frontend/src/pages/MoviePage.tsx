import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import StarRating from '../components/StarRating';
import AlgorithmSelector from '../components/AlgorithmSelector';
import MovieGrid from '../components/MovieGrid';
import { getMovieDetail, getRecommendations, getCollabRecommendations } from '../services/api';
import type { MovieDetail, RecommendationDTO, AlgorithmType } from '../types/movie';

export default function MoviePage() {
  const { id } = useParams<{ id: string }>();
  const movieId = Number(id);

  const [movie, setMovie] = useState<MovieDetail | null>(null);
  const [recs, setRecs] = useState<RecommendationDTO[]>([]);
  const [algorithm, setAlgorithm] = useState<AlgorithmType>('content-embedding');
  const [userId, setUserId] = useState<number>(1);
  const [loading, setLoading] = useState(true);
  const [recsLoading, setRecsLoading] = useState(false);

  const needsUser = algorithm === 'collab' || algorithm.startsWith('hybrid');

  // Fetch movie detail
  useEffect(() => {
    if (!movieId) return;
    setLoading(true);
    getMovieDetail(movieId)
      .then(setMovie)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [movieId]);

  // Fetch recommendations when algorithm or userId changes
  useEffect(() => {
    if (!movieId) return;
    setRecsLoading(true);

    const fetchRecs = async () => {
      try {
        if (algorithm === 'collab') {
          const data = await getCollabRecommendations(userId, 10);
          setRecs(data);
        } else {
          const data = await getRecommendations(algorithm, movieId, 10, needsUser ? userId : undefined);
          setRecs(data);
        }
      } catch (err) {
        console.error(err);
        setRecs([]);
      } finally {
        setRecsLoading(false);
      }
    };

    fetchRecs();
  }, [movieId, algorithm, userId, needsUser]);

  if (loading) {
    return (
      <div className="min-h-screen pt-24 flex items-center justify-center">
        <div className="animate-spin text-4xl">⏳</div>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className="min-h-screen pt-24 text-center text-gray-500">
        <p className="text-4xl mb-4">😞</p>
        <p>Movie not found</p>
      </div>
    );
  }

  const genreList = movie.genres.split(',').map((g) => g.trim()).filter(Boolean);

  return (
    <div className="min-h-screen pt-20">
      {/* Movie Detail Header */}
      <section className="relative">
        {/* Background blur */}
        {movie.poster_url && (
          <div
            className="absolute inset-0 bg-cover bg-center opacity-10 blur-2xl scale-110"
            style={{ backgroundImage: `url(${movie.poster_url})` }}
          />
        )}
        <div className="absolute inset-0 bg-gradient-to-b from-surface-900/80 to-surface-900" />

        <div className="relative max-w-7xl mx-auto px-6 py-12 flex flex-col md:flex-row gap-8">
          {/* Poster */}
          <div className="w-64 flex-shrink-0 mx-auto md:mx-0">
            <div className="aspect-[2/3] rounded-2xl overflow-hidden shadow-2xl shadow-primary-900/50">
              {movie.poster_url ? (
                <img src={movie.poster_url} alt={movie.title} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-surface-700 flex items-center justify-center text-6xl text-gray-600">🎬</div>
              )}
            </div>
          </div>

          {/* Info */}
          <div className="flex-1 space-y-4">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-100">{movie.title}</h1>

            <StarRating rating={movie.avg_rating} size="md" />

            <div className="flex flex-wrap gap-2">
              {genreList.map((g) => (
                <span key={g} className="genre-badge">{g}</span>
              ))}
            </div>

            <p className="text-gray-400 leading-relaxed max-w-2xl">{movie.overview}</p>

            {movie.cast && (
              <div>
                <span className="text-xs text-gray-500 uppercase tracking-wider">Cast</span>
                <p className="text-gray-300 text-sm mt-1">{movie.cast.split(',').slice(0, 5).join(', ')}</p>
              </div>
            )}

            {movie.trailer_key && (
              <a
                href={`https://www.youtube.com/watch?v=${movie.trailer_key}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary inline-flex items-center gap-2"
              >
                ▶️ Watch Trailer
              </a>
            )}
          </div>
        </div>
      </section>

      {/* Recommendations */}
      <section className="max-w-7xl mx-auto px-6 py-12 space-y-6">
        <h2 className="text-2xl font-bold text-gray-100">Recommendations</h2>

        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <AlgorithmSelector selected={algorithm} onSelect={setAlgorithm} />

          {needsUser && (
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">User ID:</label>
              <input
                type="number"
                value={userId}
                onChange={(e) => setUserId(Number(e.target.value) || 1)}
                className="input-dark w-20 text-center !py-2"
                min={1}
              />
            </div>
          )}
        </div>

        <MovieGrid movies={recs} loading={recsLoading} emptyMessage="No recommendations found for this algorithm" />
      </section>
    </div>
  );
}
