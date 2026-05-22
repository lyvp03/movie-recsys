from sqlmodel import Session, select, func

from domain.entities.rating import Rating
from domain.interfaces.i_rating_repo import IRatingRepository
from infrastructure.db.models import RatingTable


class PostgresRatingRepository(IRatingRepository):
    def __init__(self, session: Session):
        self._session = session

    def _to_entity(self, row: RatingTable) -> Rating:
        return Rating(
            id=row.id,
            user_id=row.user_id,
            movie_id=row.movie_id,
            rating=row.rating,
            rated_at=row.rated_at,
        )

    def get_by_user(self, user_id: int) -> list[Rating]:
        rows = self._session.exec(
            select(RatingTable).where(RatingTable.user_id == user_id)
        ).all()
        return [self._to_entity(row) for row in rows]

    def get_all(self) -> list[Rating]:
        rows = self._session.exec(select(RatingTable)).all()
        return [self._to_entity(row) for row in rows]

    def get_user_rated_movie_ids(self, user_id: int) -> set[int]:
        # Optimize by only selecting movie_id
        rows = self._session.exec(
            select(RatingTable.movie_id).where(RatingTable.user_id == user_id)
        ).all()
        return set(rows)

    def count_by_user(self, user_id: int) -> int:
        count = self._session.exec(
            select(func.count(RatingTable.id)).where(RatingTable.user_id == user_id)
        ).one()
        return count
