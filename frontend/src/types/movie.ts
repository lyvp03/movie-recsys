export interface MovieSearchResult {
  movie_id: number;
  tmdb_id: number;
  title: string;
  genres: string;
  avg_rating: number;
  overview: string;
  poster_url?: string;
}

export interface MovieDetail {
  movie_id: number;
  tmdb_id: number;
  title: string;
  genres: string;
  cast: string;
  keywords: string;
  overview: string;
  avg_rating: number;
  poster_url: string | null;
  trailer_key: string | null;
}

export interface RecommendationDTO {
  movie_id: number;
  tmdb_id: number;
  title: string;
  genres: string;
  similarity_score: number;
}

export interface EmotionRecommendationDTO extends RecommendationDTO {
  emotion_tags: Record<string, number> | null;
}

export type AlgorithmType = 'content-tfidf' | 'content-embedding' | 'collab' | 'hybrid-tfidf' | 'hybrid-embedding';
