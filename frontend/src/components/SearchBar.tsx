import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDebounce } from '../hooks/useDebounce';
import { searchMovies } from '../services/api';
import type { MovieSearchResult } from '../types/movie';

interface SearchBarProps {
  placeholder?: string;
  className?: string;
}

export default function SearchBar({ placeholder = 'Search movies...', className = '' }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<MovieSearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debouncedQuery = useDebounce(query, 300);
  const navigate = useNavigate();
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (debouncedQuery.length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    searchMovies(debouncedQuery, 8)
      .then(setResults)
      .catch(() => setResults([]))
      .finally(() => setLoading(false));
  }, [debouncedQuery]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={wrapperRef} className={`relative ${className}`}>
      <div className="relative">
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">🔍</span>
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className="input-dark pl-12"
        />
        {loading && (
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 animate-spin">⏳</span>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 glass-card overflow-hidden z-50 max-h-96 overflow-y-auto">
          {results.map((movie) => (
            <button
              key={movie.movie_id}
              onClick={() => {
                navigate(`/movie/${movie.movie_id}`);
                setIsOpen(false);
                setQuery('');
              }}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-white/10 transition-colors text-left"
            >
              <span className="text-2xl">🎬</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-200 truncate">{movie.title}</p>
                <p className="text-xs text-gray-500 truncate">{movie.genres}</p>
              </div>
              <span className="text-xs text-accent font-medium">{movie.avg_rating.toFixed(1)} ★</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
