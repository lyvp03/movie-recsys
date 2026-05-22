import pytest
from sqlmodel import Session, SQLModel, create_engine
from domain.entities.emotion import EmotionVector
from infrastructure.db.models import MovieTable
from infrastructure.db.postgres_emotion_repo import PostgresEmotionRepository

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="repo")
def repo_fixture(session: Session):
    return PostgresEmotionRepository(session)

def test_save_and_get(session: Session, repo: PostgresEmotionRepository):
    # Create a dummy movie first due to foreign key constraints (sqlite doesn't strictly enforce by default but good practice)
    movie = MovieTable(tmdb_id=1, title="Test", genres="Action", cast="Cast", keywords="kw", overview="ow", avg_rating=5.0)
    session.add(movie)
    session.commit()
    
    vector = EmotionVector(joy=0.8, fear=0.2)
    repo.save(movie.id, vector)
    
    retrieved = repo.get_by_movie_id(movie.id)
    assert retrieved is not None
    assert retrieved.joy == 0.8
    assert retrieved.fear == 0.2
    assert retrieved.sadness == 0.0

def test_get_not_found(repo: PostgresEmotionRepository):
    assert repo.get_by_movie_id(999) is None

def test_save_upserts_existing(session: Session, repo: PostgresEmotionRepository):
    movie = MovieTable(tmdb_id=2, title="Test 2", genres="Action", cast="Cast", keywords="kw", overview="ow", avg_rating=5.0)
    session.add(movie)
    session.commit()
    
    vector1 = EmotionVector(joy=0.5)
    repo.save(movie.id, vector1)
    
    vector2 = EmotionVector(joy=0.1, anger=0.9)
    repo.save(movie.id, vector2)
    
    retrieved = repo.get_by_movie_id(movie.id)
    assert retrieved.joy == 0.1
    assert retrieved.anger == 0.9

def test_get_by_movie_ids(session: Session, repo: PostgresEmotionRepository):
    m1 = MovieTable(tmdb_id=3, title="M1", genres="Action", cast="C", keywords="k", overview="o", avg_rating=5.0)
    m2 = MovieTable(tmdb_id=4, title="M2", genres="Action", cast="C", keywords="k", overview="o", avg_rating=5.0)
    session.add_all([m1, m2])
    session.commit()
    
    repo.save(m1.id, EmotionVector(joy=1.0))
    repo.save(m2.id, EmotionVector(fear=1.0))
    
    results = repo.get_by_movie_ids([m1.id, m2.id, 999])
    assert len(results) == 2
    assert results[m1.id].joy == 1.0
    assert results[m2.id].fear == 1.0
    assert 999 not in results
