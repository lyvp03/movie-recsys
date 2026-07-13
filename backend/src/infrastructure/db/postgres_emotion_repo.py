from sqlmodel import Session, select
from domain.entities.emotion import EmotionVector
from domain.interfaces.i_emotion_repo import IEmotionRepository
from infrastructure.db.models import EmotionVectorTable

class PostgresEmotionRepository(IEmotionRepository):
    def __init__(self, session: Session):
        self._session = session

    def save(self, movie_id: int, vector: EmotionVector) -> None:
        statement = select(EmotionVectorTable).where(EmotionVectorTable.movie_id == movie_id)
        existing = self._session.exec(statement).first()

        if existing:
            existing.joy = vector.joy
            existing.trust = vector.trust
            existing.fear = vector.fear
            existing.surprise = vector.surprise
            existing.sadness = vector.sadness
            existing.disgust = vector.disgust
            existing.anger = vector.anger
            existing.anticipation = vector.anticipation
            self._session.add(existing)
        else:
            new_record = EmotionVectorTable(
                movie_id=movie_id,
                joy=vector.joy,
                trust=vector.trust,
                fear=vector.fear,
                surprise=vector.surprise,
                sadness=vector.sadness,
                disgust=vector.disgust,
                anger=vector.anger,
                anticipation=vector.anticipation,
            )
            self._session.add(new_record)
            
        self._session.commit()

    def get_by_movie_id(self, movie_id: int) -> EmotionVector | None:
        statement = select(EmotionVectorTable).where(EmotionVectorTable.movie_id == movie_id)
        record = self._session.exec(statement).first()
        
        if not record:
            return None
            
        return EmotionVector(
            joy=record.joy,
            trust=record.trust,
            fear=record.fear,
            surprise=record.surprise,
            sadness=record.sadness,
            disgust=record.disgust,
            anger=record.anger,
            anticipation=record.anticipation,
        )

    def get_by_movie_ids(self, movie_ids: list[int]) -> dict[int, EmotionVector]:
        if not movie_ids:
            return {}
            
        statement = select(EmotionVectorTable).where(EmotionVectorTable.movie_id.in_(movie_ids))
        records = self._session.exec(statement).all()
        
        result = {}
        for r in records:
            result[r.movie_id] = EmotionVector(
                joy=r.joy,
                trust=r.trust,
                fear=r.fear,
                surprise=r.surprise,
                sadness=r.sadness,
                disgust=r.disgust,
                anger=r.anger,
                anticipation=r.anticipation,
            )
        return result

    def get_all(self) -> dict[int, EmotionVector]:
        records = self._session.exec(select(EmotionVectorTable)).all()
        result = {}
        for r in records:
            result[r.movie_id] = EmotionVector(
                joy=r.joy,
                trust=r.trust,
                fear=r.fear,
                surprise=r.surprise,
                sadness=r.sadness,
                disgust=r.disgust,
                anger=r.anger,
                anticipation=r.anticipation,
            )
        return result
