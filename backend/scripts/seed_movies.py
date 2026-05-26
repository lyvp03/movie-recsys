"""Seed the database with MovieLens + TMDB movie data.

Pipeline:
  1. Parse movies.csv → extract title (strip year), year, genres (pipe-sep → list)
  2. Join movies + links.csv on movieId → get tmdbId per movie
  3. Parse TMDB CSVs: json.loads() genres/cast/keywords; cast[:5] names only
  4. Left join MovieLens+links → TMDB on tmdb_id (keep all ML rows)
  4.5 Fetch missing TMDB data from API (rate-limited 40 req/10s)
  5. Apply fallbacks for null overview/genres/cast
  6. Compute avg_rating + rating_count from ratings.csv, merge into movies
  7. Upsert movies → DB (on tmdb_id conflict)
  8. Batch insert ratings → DB (1000-row batches)

TMDB coverage cases:
  Case 1: tmdb_id present, not in CSV → fetch from TMDB API
  Case 2: no tmdb_id (links.csv missing) → keep in DB for CF, skip TF-IDF
  Case 3: overview still null after API → fallback to "title (year)"
  Case 4: genres/cast null after fetch → empty string, no "null" literal

Validation:
  - assert movies count >= expected threshold
  - assert ratings count matches source
  - log TMDB coverage stats
"""

import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
import httpx
from sqlalchemy import text

# ---------------------------------------------------------------------------
# Bootstrap: add backend/src to sys.path so infrastructure modules resolve
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND_SRC = _SCRIPT_DIR.parent / "src"
sys.path.insert(0, str(_BACKEND_SRC))

load_dotenv()

from infrastructure.db.connection import get_engine  # noqa: E402
from infrastructure.db.models import MovieTable, RatingTable, UserTable  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DATA_ROOT = _SCRIPT_DIR.parent.parent / "data"
_ML_DIR = _DATA_ROOT / "ml-latest-small"
_TMDB_DIR = _DATA_ROOT / "tmdb50"

MOVIES_CSV = _ML_DIR / "movies.csv"
RATINGS_CSV = _ML_DIR / "ratings.csv"
LINKS_CSV = _ML_DIR / "links.csv"
TMDB_MOVIES_CSV = _TMDB_DIR / "tmdb_5000_movies.csv"
TMDB_CREDITS_CSV = _TMDB_DIR / "tmdb_5000_credits.csv"

RATING_BATCH_SIZE = 1000
MIN_EXPECTED_MOVIES = 9700  # ml-latest-small has 9742
YEAR_REGEX = re.compile(r"\s*\((\d{4})\)\s*$")
TOP_CAST_COUNT = 5

# TMDB API rate limiting: free tier = 40 requests per 10 seconds
TMDB_RATE_LIMIT_BATCH = 40
TMDB_RATE_LIMIT_WINDOW_SECONDS = 10
TMDB_REQUEST_TIMEOUT_SECONDS = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ===================================================================
# Step 1 — Parse MovieLens movies.csv
# ===================================================================
def parse_movielens_movies(path: Path) -> pd.DataFrame:
    """Load movies.csv → DataFrame with movieId, title, year, genres (list)."""
    df = pd.read_csv(path, encoding="utf-8")

    titles_clean: list[str] = []
    years: list[int | None] = []
    genres_list: list[str] = []

    for _, row in df.iterrows():
        raw_title = str(row["title"])
        match = YEAR_REGEX.search(raw_title)
        if match:
            titles_clean.append(YEAR_REGEX.sub("", raw_title).strip())
            years.append(int(match.group(1)))
        else:
            titles_clean.append(raw_title.strip())
            years.append(None)

        raw_genres = str(row["genres"])
        if raw_genres == "(no genres listed)":
            genres_list.append("")
        else:
            genres_list.append(raw_genres.replace("|", ","))

    df["title_clean"] = titles_clean
    df["year"] = years
    df["genres_csv"] = genres_list

    logger.info("Parsed %d movies from %s", len(df), path.name)
    return df[["movieId", "title_clean", "year", "genres_csv"]]


# ===================================================================
# Step 2 — Join with links.csv to get tmdbId
# ===================================================================
def join_links(movies_df: pd.DataFrame, links_path: Path) -> pd.DataFrame:
    """Left-join movies with links.csv on movieId → add tmdbId column."""
    links = pd.read_csv(links_path)
    merged = movies_df.merge(links[["movieId", "tmdbId"]], on="movieId", how="left")
    has_tmdb = merged["tmdbId"].notna().sum()
    logger.info(
        "Joined links: %d/%d movies have a tmdbId", has_tmdb, len(merged)
    )
    return merged


# ===================================================================
# Step 3 — Parse TMDB CSVs (movies + credits)
# ===================================================================
def _safe_json_names(raw: str, key: str = "name", limit: int | None = None) -> str:
    """Parse a JSON list-of-dicts string; return comma-separated names."""
    if not isinstance(raw, str) or not raw.strip():
        return ""
    try:
        items = json.loads(raw)
        names = [item[key] for item in items if key in item]
        if limit is not None:
            names = names[:limit]
        return ",".join(names)
    except (json.JSONDecodeError, TypeError):
        return ""


def parse_tmdb(
    movies_path: Path, credits_path: Path
) -> pd.DataFrame:
    """Load TMDB CSVs → DataFrame with tmdb_id, genres, cast, keywords, overview."""
    tmdb = pd.read_csv(movies_path, encoding="utf-8")
    credits = pd.read_csv(credits_path, encoding="utf-8")

    # Rename id columns for clarity
    tmdb = tmdb.rename(columns={"id": "tmdb_id"})
    credits = credits.rename(columns={"movie_id": "tmdb_id"})

    # Parse JSON columns in tmdb
    tmdb["genres_csv"] = tmdb["genres"].apply(lambda g: _safe_json_names(g))
    tmdb["keywords_csv"] = tmdb["keywords"].apply(lambda k: _safe_json_names(k))
    tmdb["overview_clean"] = tmdb["overview"].fillna("")

    # Parse cast from credits (top 5 names)
    credits["cast_csv"] = credits["cast"].apply(
        lambda c: _safe_json_names(c, limit=TOP_CAST_COUNT)
    )

    # Merge tmdb + credits on tmdb_id
    tmdb = tmdb.merge(
        credits[["tmdb_id", "cast_csv"]], on="tmdb_id", how="left"
    )
    tmdb["cast_csv"] = tmdb["cast_csv"].fillna("")

    logger.info("Parsed %d TMDB movies with credits", len(tmdb))
    return tmdb[["tmdb_id", "genres_csv", "cast_csv", "keywords_csv", "overview_clean"]]


# ===================================================================
# Step 4 — Left join MovieLens → TMDB
# ===================================================================
def merge_ml_tmdb(
    ml_df: pd.DataFrame, tmdb_df: pd.DataFrame
) -> pd.DataFrame:
    """Left join ML+links onto TMDB on tmdbId/tmdb_id. ML rows always kept."""
    merged = ml_df.merge(
        tmdb_df,
        left_on="tmdbId",
        right_on="tmdb_id",
        how="left",
        suffixes=("_ml", "_tmdb"),
    )

    # Prefer TMDB genres/overview when available; fall back to ML genres
    merged["final_genres"] = merged["genres_csv_tmdb"].fillna(
        merged["genres_csv_ml"]
    )
    merged["final_cast"] = merged["cast_csv"].fillna("")
    merged["final_keywords"] = merged["keywords_csv"].fillna("")
    merged["final_overview"] = merged["overview_clean"].fillna("")

    tmdb_matched = merged["tmdb_id"].notna().sum()
    tmdb_missing = merged["tmdb_id"].isna().sum()
    logger.info(
        "Left join result: %d total | %d with TMDB data | %d without",
        len(merged),
        tmdb_matched,
        tmdb_missing,
    )
    return merged


# ===================================================================
# Step 4.5 — Fetch missing TMDB data from API
# ===================================================================
def _fetch_tmdb_movie(client: httpx.Client, tmdb_id: int) -> dict | None:
    """Fetch a single movie from TMDB API with appended credits."""
    base_url = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
    api_key = os.getenv("TMDB_API_KEY", "")
    if not api_key:
        return None

    url = f"{base_url}/movie/{tmdb_id}"
    params = {
        "api_key": api_key,
        "append_to_response": "credits,keywords",
    }
    try:
        resp = client.get(url, params=params, timeout=TMDB_REQUEST_TIMEOUT_SECONDS)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        logger.warning("TMDB API error for tmdb_id=%d: %s", tmdb_id, exc)
        return None


def _parse_api_response(data: dict) -> dict:
    """Extract genres, cast (top 5), keywords, overview from API response."""
    genres = ",".join(g["name"] for g in data.get("genres", []) if "name" in g)

    credits = data.get("credits", {})
    cast_list = credits.get("cast", [])
    cast = ",".join(
        c["name"] for c in cast_list[:TOP_CAST_COUNT] if "name" in c
    )

    kw_data = data.get("keywords", {})
    kw_list = kw_data.get("keywords", [])  # nested under "keywords" key
    keywords = ",".join(k["name"] for k in kw_list if "name" in k)

    overview = data.get("overview", "") or ""

    return {
        "genres": genres,
        "cast": cast,
        "keywords": keywords,
        "overview": overview,
    }


def fetch_missing_tmdb_data(merged: pd.DataFrame) -> pd.DataFrame:
    """Fetch TMDB API data for movies that have tmdb_id but no CSV match.

    Rate-limited to TMDB_RATE_LIMIT_BATCH requests per window.
    """
    api_key = os.getenv("TMDB_API_KEY", "")
    if not api_key or api_key == "your_key_here":
        logger.warning("TMDB_API_KEY not set — skipping API fetch")
        return merged

    # Case 1: has tmdb_id but overview is empty (not matched in CSV)
    needs_fetch = merged[
        (merged["tmdbId"].notna()) & (merged["final_overview"] == "")
    ]
    total_to_fetch = len(needs_fetch)

    if total_to_fetch == 0:
        logger.info("All movies with tmdb_id already have TMDB data")
        return merged

    logger.info(
        "Fetching TMDB API data for %d movies missing from CSV...",
        total_to_fetch,
    )

    fetched_count = 0
    api_errors = 0
    batch_start_time = time.monotonic()
    requests_in_window = 0

    with httpx.Client() as client:
        for idx in needs_fetch.index:
            tmdb_id = int(merged.at[idx, "tmdbId"])

            # Rate limiting: pause if we've hit the batch limit
            if requests_in_window >= TMDB_RATE_LIMIT_BATCH:
                elapsed = time.monotonic() - batch_start_time
                remaining = TMDB_RATE_LIMIT_WINDOW_SECONDS - elapsed
                if remaining > 0:
                    logger.info(
                        "Rate limit: sleeping %.1fs (%d/%d fetched)",
                        remaining,
                        fetched_count,
                        total_to_fetch,
                    )
                    time.sleep(remaining)
                batch_start_time = time.monotonic()
                requests_in_window = 0

            data = _fetch_tmdb_movie(client, tmdb_id)
            requests_in_window += 1

            if data is None:
                api_errors += 1
                continue

            parsed = _parse_api_response(data)
            if parsed["overview"]:
                merged.at[idx, "final_overview"] = parsed["overview"]
            if parsed["genres"]:
                merged.at[idx, "final_genres"] = parsed["genres"]
            if parsed["cast"]:
                merged.at[idx, "final_cast"] = parsed["cast"]
            if parsed["keywords"]:
                merged.at[idx, "final_keywords"] = parsed["keywords"]

            fetched_count += 1

            if fetched_count % 100 == 0:
                logger.info(
                    "  Progress: %d/%d fetched", fetched_count, total_to_fetch
                )

    logger.info(
        "TMDB API fetch complete: %d enriched, %d errors/not-found",
        fetched_count,
        api_errors,
    )
    return merged


# ===================================================================
# Step 5 — Apply fallbacks for null fields
# ===================================================================
def apply_fallbacks(merged: pd.DataFrame) -> pd.DataFrame:
    """Apply fallback values for movies still missing TMDB fields.

    Case 3: overview null → use 'title (year)' as feature string
    Case 4: genres/cast null → empty string (no 'null' literal)
    """
    for idx, row in merged.iterrows():
        overview = str(row.get("final_overview", "") or "")
        if not overview.strip():
            title = str(row.get("title_clean", ""))
            year = row.get("year")
            if pd.notna(year):
                merged.at[idx, "final_overview"] = f"{title} ({int(year)})"
            else:
                merged.at[idx, "final_overview"] = title

        # Ensure no 'nan'/'None' literal leaks
        for col in ("final_genres", "final_cast", "final_keywords"):
            val = str(row.get(col, "") or "")
            if val.lower() in ("nan", "none", "null"):
                merged.at[idx, col] = ""

    fallback_count = merged[
        merged["final_overview"].apply(
            lambda x: bool(re.match(r"^[^.]{1,80}$", str(x)))
        )
    ].shape[0]
    logger.info(
        "Fallbacks applied: %d movies using short overview (title-year or minimal)",
        fallback_count,
    )
    return merged


# ===================================================================
# Step 6 — Compute avg_rating + rating_count
# ===================================================================
def compute_rating_stats(ratings_path: Path) -> pd.DataFrame:
    """Return DataFrame with movieId, avg_rating, rating_count."""
    ratings = pd.read_csv(ratings_path)
    stats = (
        ratings.groupby("movieId")["rating"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "avg_rating", "count": "rating_count"})
    )
    stats["avg_rating"] = stats["avg_rating"].round(2)
    logger.info(
        "Rating stats: %d movies rated, total %d ratings",
        len(stats),
        ratings["rating"].count(),
    )
    return stats


# ===================================================================
# Step 6 — Upsert movies into DB
# ===================================================================
def upsert_movies(session: Session, movies_df: pd.DataFrame) -> int:
    """Insert/update movies into the movies table. Returns rows affected."""
    inserted = 0

    for _, row in movies_df.iterrows():
        tmdb_id_val = row.get("tmdbId")
        # Skip movies without a tmdb_id — the DB column is NOT NULL
        if pd.isna(tmdb_id_val):
            continue

        tmdb_id_int = int(tmdb_id_val)

        # Check for existing row (upsert)
        existing = session.exec(
            select(MovieTable).where(MovieTable.tmdb_id == tmdb_id_int)
        ).first()

        avg_rating = float(row.get("avg_rating", 0.0) or 0.0)
        title = str(row.get("title_clean", ""))
        genres = str(row.get("final_genres", "") or "")
        cast_str = str(row.get("final_cast", "") or "")
        keywords = str(row.get("final_keywords", "") or "")
        overview = str(row.get("final_overview", "") or "")

        if existing:
            existing.title = title
            existing.genres = genres
            existing.cast = cast_str
            existing.keywords = keywords
            existing.overview = overview
            existing.avg_rating = avg_rating
            session.add(existing)
        else:
            movie = MovieTable(
                tmdb_id=tmdb_id_int,
                title=title,
                genres=genres,
                cast=cast_str,
                keywords=keywords,
                overview=overview,
                avg_rating=avg_rating,
            )
            session.add(movie)
        inserted += 1

    session.commit()
    logger.info("Upserted %d movies into DB", inserted)
    return inserted


# ===================================================================
# Step 6.5 — Ensure users exist for all user_ids in ratings
# ===================================================================
def ensure_users(session: Session, ratings_path: Path) -> None:
    """Create user rows for every distinct userId in ratings."""
    ratings = pd.read_csv(ratings_path)
    user_ids = sorted(ratings["userId"].unique())

    existing_ids = set(
        session.exec(select(UserTable.id)).all()
    )

    new_users = [
        UserTable(id=int(uid))
        for uid in user_ids
        if uid not in existing_ids
    ]
    if new_users:
        session.add_all(new_users)
        session.commit()
    logger.info(
        "Users: %d existing, %d created → %d total",
        len(existing_ids),
        len(new_users),
        len(existing_ids) + len(new_users),
    )


# ===================================================================
# Step 7 — Batch insert ratings
# ===================================================================
def _build_movie_id_lookup(session: Session) -> dict[int, int]:
    """Map tmdb_id → movies.id (primary key) for FK resolution."""
    rows = session.exec(select(MovieTable.id, MovieTable.tmdb_id)).all()
    return {tmdb_id: pk for pk, tmdb_id in rows}


def _build_movieid_to_tmdbid(links_path: Path) -> dict[int, int]:
    """Map MovieLens movieId → tmdbId from links.csv."""
    links = pd.read_csv(links_path)
    mapping: dict[int, int] = {}
    for _, row in links.iterrows():
        if pd.notna(row["tmdbId"]):
            mapping[int(row["movieId"])] = int(row["tmdbId"])
    return mapping


def insert_ratings(
    session: Session,
    ratings_path: Path,
    links_path: Path,
) -> int:
    """Batch-insert ratings. Returns total rows inserted."""
    ratings = pd.read_csv(ratings_path)
    ml_to_tmdb = _build_movieid_to_tmdbid(links_path)
    tmdb_to_pk = _build_movie_id_lookup(session)

    # Clear existing ratings to avoid duplicates on re-run
    session.exec(text("DELETE FROM ratings"))  # type: ignore[call-overload]
    session.commit()

    total_inserted = 0
    batch: list[RatingTable] = []
    skipped = 0

    for _, row in ratings.iterrows():
        ml_movie_id = int(row["movieId"])
        tmdb_id = ml_to_tmdb.get(ml_movie_id)
        if tmdb_id is None:
            skipped += 1
            continue

        movie_pk = tmdb_to_pk.get(tmdb_id)
        if movie_pk is None:
            skipped += 1
            continue

        rated_at = datetime.fromtimestamp(int(row["timestamp"]), tz=timezone.utc)

        batch.append(
            RatingTable(
                user_id=int(row["userId"]),
                movie_id=movie_pk,
                rating=float(row["rating"]),
                rated_at=rated_at,
            )
        )

        if len(batch) >= RATING_BATCH_SIZE:
            session.add_all(batch)
            session.commit()
            total_inserted += len(batch)
            batch = []

    # Flush remaining
    if batch:
        session.add_all(batch)
        session.commit()
        total_inserted += len(batch)

    logger.info(
        "Inserted %d ratings (%d skipped — no matching movie in DB)",
        total_inserted,
        skipped,
    )
    return total_inserted


# ===================================================================
# Validation
# ===================================================================
def validate(session: Session, expected_ratings: int) -> None:
    """Post-insert sanity checks."""
    movie_count = session.exec(
        text("SELECT count(*) FROM movies")
    ).scalar()
    rating_count = session.exec(
        text("SELECT count(*) FROM ratings")
    ).scalar()
    tmdb_with_overview = session.exec(
        text("SELECT count(*) FROM movies WHERE overview != ''")
    ).scalar()
    tmdb_without_overview = session.exec(
        text("SELECT count(*) FROM movies WHERE overview = ''")
    ).scalar()

    logger.info("=== Validation ===")
    logger.info("Movies in DB        : %d", movie_count)
    logger.info("Ratings in DB       : %d", rating_count)
    logger.info("With TMDB overview   : %d", tmdb_with_overview)
    logger.info("Without TMDB overview: %d", tmdb_without_overview)

    assert movie_count >= MIN_EXPECTED_MOVIES, (
        f"Expected >= {MIN_EXPECTED_MOVIES} movies, got {movie_count}"
    )
    logger.info(
        "Inserted %d ratings (source has %d — diff is movies not in DB)",
        rating_count,
        expected_ratings,
    )


# ===================================================================
# Main
# ===================================================================
def main() -> None:
    """Run the full seed pipeline."""
    logger.info("=" * 60)
    logger.info("STARTING SEED: MovieLens + TMDB → PostgreSQL")
    logger.info("=" * 60)

    # Verify data files exist
    for path in (MOVIES_CSV, RATINGS_CSV, LINKS_CSV, TMDB_MOVIES_CSV, TMDB_CREDITS_CSV):
        if not path.exists():
            raise FileNotFoundError(f"Missing data file: {path}")

    # Step 1: Parse MovieLens
    ml_movies = parse_movielens_movies(MOVIES_CSV)

    # Step 2: Join links
    ml_with_links = join_links(ml_movies, LINKS_CSV)

    # Step 3: Parse TMDB
    tmdb = parse_tmdb(TMDB_MOVIES_CSV, TMDB_CREDITS_CSV)

    # Step 4: Left join
    merged = merge_ml_tmdb(ml_with_links, tmdb)

    # Step 4.5: Fetch missing TMDB data from API
    merged = fetch_missing_tmdb_data(merged)

    # Step 5: Apply fallbacks for null fields
    merged = apply_fallbacks(merged)

    # Step 6: Rating stats
    rating_stats = compute_rating_stats(RATINGS_CSV)
    merged = merged.merge(rating_stats, on="movieId", how="left")
    merged["avg_rating"] = merged["avg_rating"].fillna(0.0)
    merged["rating_count"] = merged["rating_count"].fillna(0).astype(int)

    source_rating_count = len(pd.read_csv(RATINGS_CSV))

    # Steps 7 & 8: Write to DB
    with Session(get_engine()) as session:
        upsert_movies(session, merged)
        ensure_users(session, RATINGS_CSV)
        insert_ratings(session, RATINGS_CSV, LINKS_CSV)
        validate(session, source_rating_count)

    logger.info("=" * 60)
    logger.info("SEED COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
