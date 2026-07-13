import { useState } from 'react';
import MovieGrid from '../components/MovieGrid';
import { getEmotionRecommendations } from '../services/api';
import type { EmotionRecommendationDTO } from '../types/movie';

const EXAMPLE_QUERIES = [
  'phim gây cảm giác cô đơn và hy vọng trong không gian',
  'a heartwarming family comedy',
  'dark thriller with unexpected twists',
  'romantic movie that makes you cry',
  'exciting adventure in a fantasy world',
];

export default function EmotionPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<EmotionRecommendationDTO[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (searchQuery?: string) => {
    const q = searchQuery || query;
    if (q.length < 3) return;

    setLoading(true);
    setError('');
    try {
      const data = await getEmotionRecommendations(q, 10);
      setResults(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to get recommendations');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen pt-16">
      {/* Hero */}
      <section className="relative py-20 px-6 overflow-hidden">
        <div className="absolute top-10 left-1/3 w-96 h-96 bg-purple-600/10 rounded-full blur-[128px]" />
        <div className="absolute top-20 right-1/3 w-72 h-72 bg-pink-600/10 rounded-full blur-[128px]" />

        <div className="relative max-w-3xl mx-auto text-center space-y-6">
          <h1 className="text-4xl md:text-5xl font-extrabold">
            <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              💭 Emotion Search
            </span>
          </h1>
          <p className="text-gray-400 text-lg">
            Describe the feeling you want — in any language — and we'll find movies that match
          </p>

          <div className="flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Describe the emotion you're looking for..."
              className="input-dark flex-1"
            />
            <button onClick={() => handleSearch()} className="btn-primary whitespace-nowrap" disabled={loading}>
              {loading ? '⏳' : '🔍'} Search
            </button>
          </div>

          {/* Example queries */}
          <div className="flex flex-wrap justify-center gap-2">
            {EXAMPLE_QUERIES.map((eq) => (
              <button
                key={eq}
                onClick={() => {
                  setQuery(eq);
                  handleSearch(eq);
                }}
                className="text-xs px-3 py-1.5 rounded-full bg-white/5 text-gray-400 hover:bg-white/10 hover:text-gray-200 transition-all border border-white/5"
              >
                "{eq.length > 40 ? eq.slice(0, 40) + '...' : eq}"
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Results */}
      <section className="max-w-7xl mx-auto px-6 pb-20">
        {error && (
          <div className="glass-card p-4 mb-6 border-red-500/30 text-red-300 text-center">
            ⚠️ {error}
          </div>
        )}
        <MovieGrid movies={results} loading={loading} emptyMessage="Enter a query to discover movies by emotion" />
      </section>
    </div>
  );
}
