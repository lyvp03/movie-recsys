import os
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_movie_repository
from domain.exceptions import EntityNotFoundError
from infrastructure.db.postgres_movie_repo import PostgresMovieRepository

router = APIRouter(prefix="/movies", tags=["movies"])

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
TMDB_IMAGE_BASE_URL = os.getenv("TMDB_IMAGE_BASE_URL", "https://image.tmdb.org/t/p/w500")


@router.get("/search")
def search_movies(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, ge=1, le=100),
    repo: PostgresMovieRepository = Depends(get_movie_repository),
):
    """Search movies by title (autocomplete)."""
    movies = repo.search_by_title(q, limit)
    return [
        {
            "movie_id": m.id,
            "tmdb_id": m.tmdb_id,
            "title": m.title,
            "genres": m.genres,
            "avg_rating": m.avg_rating,
            "overview": m.overview[:200] if m.overview else "",
        }
        for m in movies
    ]


@router.get("/popular")
def get_popular_movies(
    limit: int = Query(default=20, ge=1, le=100),
    repo: PostgresMovieRepository = Depends(get_movie_repository),
):
    """Get top popular movies for homepage."""
    movies = repo.get_popular(limit)
    return [
        {
            "movie_id": m.id,
            "tmdb_id": m.tmdb_id,
            "title": m.title,
            "genres": m.genres,
            "avg_rating": m.avg_rating,
            "overview": m.overview[:200] if m.overview else "",
        }
        for m in movies
    ]


@router.get("/{movie_id}")
def get_movie_detail(
    movie_id: int,
    repo: PostgresMovieRepository = Depends(get_movie_repository),
):
    """Get detailed movie info including TMDB poster."""
    try:
        movie = repo.get_by_id(movie_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Fetch poster from TMDB
    poster_url = None
    trailer_key = None
    if movie.tmdb_id and TMDB_API_KEY:
        try:
            with httpx.Client(timeout=5) as client:
                # Get movie details for poster
                resp = client.get(
                    f"{TMDB_BASE_URL}/movie/{movie.tmdb_id}",
                    params={"api_key": TMDB_API_KEY},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    poster_path = data.get("poster_path")
                    if poster_path:
                        poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}"

                # Get trailer
                resp2 = client.get(
                    f"{TMDB_BASE_URL}/movie/{movie.tmdb_id}/videos",
                    params={"api_key": TMDB_API_KEY},
                )
                if resp2.status_code == 200:
                    videos = resp2.json().get("results", [])
                    for v in videos:
                        if v.get("type") == "Trailer" and v.get("site") == "YouTube":
                            trailer_key = v.get("key")
                            break
        except Exception:
            pass  # Non-critical, just skip poster/trailer

    return {
        "movie_id": movie.id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "genres": movie.genres,
        "cast": movie.cast,
        "keywords": movie.keywords,
        "overview": movie.overview,
        "avg_rating": movie.avg_rating,
        "poster_url": poster_url,
        "trailer_key": trailer_key,
    }
