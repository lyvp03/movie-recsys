import { useState } from 'react';
import { getRecommendations, getCollabRecommendations } from '../services/api';
import type { RecommendationDTO, AlgorithmType } from '../types/movie';

interface ComparisonResult {
  algorithm: string;
  label: string;
  movies: RecommendationDTO[];
  avgScore: number;
  timeMs: number;
}

export default function EvaluationPage() {
  const [movieId, setMovieId] = useState(1);
  const [userId, setUserId] = useState(1);
  const [topK, setTopK] = useState(10);
  const [results, setResults] = useState<ComparisonResult[]>([]);
  const [loading, setLoading] = useState(false);

  const runComparison = async () => {
    setLoading(true);
    const algorithms: { key: AlgorithmType | 'collab'; label: string }[] = [
      { key: 'content-tfidf', label: 'TF-IDF' },
      { key: 'content-embedding', label: 'Embedding' },
      { key: 'collab', label: 'Collaborative' },
      { key: 'hybrid-tfidf', label: 'Hybrid (TF-IDF)' },
      { key: 'hybrid-embedding', label: 'Hybrid (Embed)' },
    ];

    const comparisons: ComparisonResult[] = [];

    for (const algo of algorithms) {
      const start = performance.now();
      try {
        let movies: RecommendationDTO[];
        if (algo.key === 'collab') {
          movies = await getCollabRecommendations(userId, topK);
        } else if (algo.key.startsWith('hybrid')) {
          movies = await getRecommendations(algo.key, movieId, topK, userId);
        } else {
          movies = await getRecommendations(algo.key, movieId, topK);
        }
        const elapsed = performance.now() - start;
        const avgScore = movies.length > 0
          ? movies.reduce((sum, m) => sum + m.similarity_score, 0) / movies.length
          : 0;
        comparisons.push({ algorithm: algo.key, label: algo.label, movies, avgScore, timeMs: elapsed });
      } catch {
        const elapsed = performance.now() - start;
        comparisons.push({ algorithm: algo.key, label: algo.label, movies: [], avgScore: 0, timeMs: elapsed });
      }
    }

    setResults(comparisons);
    setLoading(false);
  };

  return (
    <div className="min-h-screen pt-20 max-w-7xl mx-auto px-6 pb-20">
      <h1 className="text-3xl font-bold mb-2">
        <span className="bg-gradient-to-r from-green-400 to-cyan-400 bg-clip-text text-transparent">
          📊 Algorithm Evaluation
        </span>
      </h1>
      <p className="text-gray-400 mb-8">Compare recommendation algorithms side by side</p>

      {/* Controls */}
      <div className="glass-card p-6 mb-8 flex flex-wrap items-end gap-6">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Movie ID</label>
          <input
            type="number"
            value={movieId}
            onChange={(e) => setMovieId(Number(e.target.value) || 1)}
            className="input-dark w-28 !py-2"
            min={1}
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">User ID</label>
          <input
            type="number"
            value={userId}
            onChange={(e) => setUserId(Number(e.target.value) || 1)}
            className="input-dark w-28 !py-2"
            min={1}
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Top K</label>
          <input
            type="number"
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value) || 10)}
            className="input-dark w-20 !py-2"
            min={1}
            max={50}
          />
        </div>
        <button onClick={runComparison} className="btn-primary" disabled={loading}>
          {loading ? '⏳ Running...' : '🚀 Run Comparison'}
        </button>
      </div>

      {/* Results Table */}
      {results.length > 0 && (
        <div className="space-y-8">
          {/* Summary Table */}
          <div className="glass-card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left p-4 text-gray-400 font-medium">Algorithm</th>
                  <th className="text-center p-4 text-gray-400 font-medium">Results</th>
                  <th className="text-center p-4 text-gray-400 font-medium">Avg Score</th>
                  <th className="text-center p-4 text-gray-400 font-medium">Response Time</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r) => (
                  <tr key={r.algorithm} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="p-4 font-medium text-gray-200">{r.label}</td>
                    <td className="p-4 text-center text-gray-300">{r.movies.length}</td>
                    <td className="p-4 text-center">
                      <span className="px-2 py-1 rounded-lg bg-primary-600/20 text-primary-300 text-xs font-mono">
                        {r.avgScore.toFixed(4)}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <span className={`px-2 py-1 rounded-lg text-xs font-mono
                        ${r.timeMs < 500 ? 'bg-green-500/20 text-green-300' :
                          r.timeMs < 2000 ? 'bg-yellow-500/20 text-yellow-300' :
                          'bg-red-500/20 text-red-300'}`}>
                        {r.timeMs.toFixed(0)}ms
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Score Bar Chart (CSS-only) */}
          <div className="glass-card p-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">Average Similarity Score</h3>
            <div className="space-y-3">
              {results.map((r) => {
                const maxScore = Math.max(...results.map((x) => x.avgScore), 0.001);
                const widthPct = (r.avgScore / maxScore) * 100;
                return (
                  <div key={r.algorithm} className="flex items-center gap-4">
                    <span className="w-32 text-sm text-gray-400 text-right">{r.label}</span>
                    <div className="flex-1 h-8 bg-white/5 rounded-lg overflow-hidden relative">
                      <div
                        className="h-full bg-gradient-to-r from-primary-600 to-primary-400 rounded-lg transition-all duration-1000"
                        style={{ width: `${widthPct}%` }}
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-mono text-gray-300">
                        {r.avgScore.toFixed(4)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Individual Results */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {results.map((r) => (
              <div key={r.algorithm} className="glass-card p-6">
                <h3 className="text-lg font-semibold text-gray-200 mb-3">{r.label}</h3>
                {r.movies.length === 0 ? (
                  <p className="text-gray-500 text-sm">No results</p>
                ) : (
                  <div className="space-y-2">
                    {r.movies.slice(0, 5).map((m, i) => (
                      <div key={m.movie_id} className="flex items-center gap-3 text-sm">
                        <span className="w-6 h-6 rounded-full bg-primary-600/30 text-primary-300 flex items-center justify-center text-xs font-bold">
                          {i + 1}
                        </span>
                        <span className="flex-1 text-gray-300 truncate">{m.title}</span>
                        <span className="text-xs font-mono text-gray-500">{m.similarity_score.toFixed(4)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
