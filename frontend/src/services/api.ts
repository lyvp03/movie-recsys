import axios from 'axios';
import type {
  MovieSearchResult,
  MovieDetail,
  RecommendationDTO,
  EmotionRecommendationDTO,
} from '../types/movie';

const api = axios.create({
  baseURL: '/api',
});

export async function searchMovies(query: string, limit = 20): Promise<MovieSearchResult[]> {
  const { data } = await api.get('/movies/search', { params: { q: query, limit } });
  return data;
}

export async function getPopularMovies(limit = 20): Promise<MovieSearchResult[]> {
  const { data } = await api.get('/movies/popular', { params: { limit } });
  return data;
}

const detailCache: Record<number, MovieDetail> = {};

export async function getMovieDetail(movieId: number): Promise<MovieDetail> {
  if (detailCache[movieId]) return detailCache[movieId];
  const { data } = await api.get(`/movies/${movieId}`);
  detailCache[movieId] = data;
  return data;
}

export async function getRecommendations(
  algorithm: string,
  movieId: number,
  topK = 10,
  userId?: number,
): Promise<RecommendationDTO[]> {
  const params: Record<string, unknown> = { top_k: topK };
  if (userId !== undefined) {
    params.user_id = userId;
  }
  const { data } = await api.get(`/recommend/${algorithm}/${movieId}`, { params });
  return data;
}

export async function getCollabRecommendations(
  userId: number,
  topK = 10,
): Promise<RecommendationDTO[]> {
  const { data } = await api.get(`/recommend/collab/${userId}`, { params: { top_k: topK } });
  return data;
}

export async function getEmotionRecommendations(
  query: string,
  topK = 10,
): Promise<EmotionRecommendationDTO[]> {
  const { data } = await api.post('/recommend/emotion', { query, top_k: topK });
  return data;
}
