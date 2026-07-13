from sqlmodel import Session, select
from typing import Sequence

from domain.entities.movie import Movie
from domain.exceptions import EntityNotFoundError
from domain.interfaces.i_movie_repo import IMovieRepository
from infrastructure.db.models import MovieTable


class PostgresMovieRepository(IMovieRepository):
    def __init__(self, session: Session):
        self._session = session

    def _to_entity(self, row: MovieTable) -> Movie:
        return Movie(
            id=row.id,
            tmdb_id=row.tmdb_id,
            title=row.title,
            genres=row.genres,
            cast=row.cast,
            keywords=row.keywords,
            overview=row.overview,
            avg_rating=row.avg_rating,
        )

    def get_by_id(self, movie_id: int) -> Movie:
        row = self._session.get(MovieTable, movie_id)
        if not row:
            raise EntityNotFoundError(f"Movie {movie_id} not found")
        return self._to_entity(row)

    def get_all(self) -> list[Movie]:
        rows = self._session.exec(select(MovieTable)).all()
        return [self._to_entity(row) for row in rows]

    def get_all_ids(self) -> list[int]:
        rows = self._session.exec(select(MovieTable.id)).all()
        return list(rows)

    def get_by_ids(self, movie_ids: list[int]) -> list[Movie]:
        if not movie_ids:
            return []
        rows = self._session.exec(select(MovieTable).where(MovieTable.id.in_(movie_ids))).all()
        return [self._to_entity(row) for row in rows]

    def filter_by_genre(self, genre: str) -> list[Movie]:
        # Simple ILIKE query for genre. Note: for array fields we'd use ANY, but genres is a string
        query = select(MovieTable).where(MovieTable.genres.ilike(f"%{genre}%"))
        rows = self._session.exec(query).all()
        return [self._to_entity(row) for row in rows]

    def search_by_title(self, query: str, limit: int = 20) -> list[Movie]:
        query_str = f"%{query}%"
        rows = self._session.exec(
            select(MovieTable)
            .where(MovieTable.title.ilike(query_str))
            .limit(limit)
        ).all()
        return [self._to_entity(row) for row in rows]

    def get_popular(self, limit: int = 20) -> list[Movie]:
        rows = self._session.exec(
            select(MovieTable)
            .order_by(MovieTable.avg_rating.desc())
            .limit(limit)
        ).all()
        return [self._to_entity(row) for row in rows]
