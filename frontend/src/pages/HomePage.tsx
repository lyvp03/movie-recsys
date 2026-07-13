import { useState, useEffect } from 'react';
import SearchBar from '../components/SearchBar';
import MovieCard from '../components/MovieCard';
import { getPopularMovies } from '../services/api';
import type { MovieSearchResult } from '../types/movie';

export default function HomePage() {
  const [popular, setPopular] = useState<MovieSearchResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPopularMovies(20)
      .then(setPopular)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen pt-16">
      {/* Hero */}
      <section className="relative py-24 px-6 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary-900/20 via-transparent to-transparent" />
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-primary-600/10 rounded-full blur-[128px]" />
        <div className="absolute top-40 right-1/4 w-72 h-72 bg-accent/10 rounded-full blur-[128px]" />

        <div className="relative max-w-3xl mx-auto text-center space-y-8">
          <h1 className="text-5xl md:text-6xl font-extrabold">
            <span className="bg-gradient-to-r from-primary-400 via-primary-300 to-accent bg-clip-text text-transparent">
              Discover Movies
            </span>
            <br />
            <span className="text-gray-300 text-3xl md:text-4xl font-semibold">
              powered by AI recommendations
            </span>
          </h1>
          <p className="text-gray-400 text-lg max-w-xl mx-auto">
            TF-IDF • Semantic Embedding • Collaborative Filtering • Emotion-Based Search
          </p>
          <SearchBar
            placeholder="Search for a movie to get recommendations..."
            className="max-w-xl mx-auto"
          />
        </div>
      </section>

      {/* Popular Movies */}
      <section className="max-w-7xl mx-auto px-6 pb-20">
        <h2 className="text-2xl font-bold text-gray-100 mb-6 flex items-center gap-2">
          <span className="text-accent">⭐</span> Popular Movies
        </h2>

        {loading ? (
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
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {popular.map((m) => (
              <MovieCard
                key={m.movie_id}
                movieId={m.movie_id}
                tmdbId={m.tmdb_id}
                title={m.title}
                genres={m.genres}
                avgRating={m.avg_rating}
                posterUrl={m.poster_url}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
