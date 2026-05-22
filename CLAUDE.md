# CLAUDE.md — Movie RecSys Agent Rules
> Read before starting any task. Check phase in `PROJECT_PLAN.md` first.

---

## 1. Architecture

Layer import order — immutable:
```
api/ → application/ → domain/
infrastructure/ → domain/
infrastructure/ → application/
```

**Always forbidden:**
- `domain/` importing from `infrastructure/` or `api/`
- `application/` importing from `infrastructure/` or `api/`

Anything outside `domain/` and `application/` must sit behind an interface. Use constructor injection — never instantiate dependencies inside a class.

```python
# ✅
class ContentBasedRecommender:
    def __init__(self, repo: IMovieRepository, similarity: ISimilarityComputer): ...

# ❌
class ContentBasedRecommender:
    def __init__(self):
        self._repo = SQLiteMovieRepository()  # violation
```

Circular imports = build failure. Enforced by `.importlinter`.

---

## 2. TDD

Red → Green → Refactor. Never write implementation before its test.

Test naming: `test_{method}_{scenario}_{expected_result}`

Unit tests must have no real DB, no real HTTP, no real file I/O — use `MagicMock(spec=Interface)` or in-memory implementations.

```python
# ✅
repo = MagicMock(spec=IMovieRepository)

# ❌
repo = SQLiteMovieRepository("test.db")
```

Coverage minimums: `domain/` 95% · `application/` 90% · `infrastructure/` 80% · `api/` 85% · overall ≥ 80%. Pre-commit enforces this.

---

## 3. Clean Code

- One responsibility per function, ~20 lines max.
- Named constants — no magic numbers (`COLD_START_THRESHOLD = 5`, not `< 5`).
- Comments explain *why*, not *what*.
- No `except Exception` — catch specific, raise domain errors.
- No `print()` — use logger.
- No TODO/FIXME without a GitHub issue number.
- Each module: ≤ 5 direct imports from other project modules.
- 200+ lines in one module is a split signal.

---

## 4. Boundaries

DTOs live in `application/dtos.py`. Never expose raw domain entities through the API — transform at the boundary. Never let domain exceptions reach HTTP responses — map them explicitly.

Frontend: `features/X/` must not import from other `features/`. Shared code goes in `components/`, `hooks/`, or `services/`.

---

## 5. Git

Format: `type(scope): message` — types: `feat` · `test` · `fix` · `refactor` · `docs`

```
feat(phase1): add ContentBasedRecommender with cosine similarity
test(phase2): add cold start fallback cases for CollaborativeRecommender
```

Branches: `main` (no direct commits) · `develop` · `phase/N-name`

---

## 6. Pre-commit

```bash
# Backend
pytest --cov=src --cov-fail-under=80
black . --check && isort . --check-only && flake8 src/ tests/
lint-imports

# Frontend
npx vitest run --coverage && npx tsc --noEmit
```

Fix all failures before committing.

---

## 7. Key Interfaces

```python
class IRecommender(ABC):
    def recommend(self, reference_id: int, top_k: int) -> list[RecommendationDTO]: ...

class IMovieRepository(ABC):
    def get_by_id(self, movie_id: int) -> Movie: ...
    def get_all(self) -> list[Movie]: ...
    def filter_by_genre(self, genre: Genre) -> list[Movie]: ...

class IVectorStore(ABC):
    def search(self, collection: str, vector: list[float], top_k: int) -> list[SearchResult]: ...
    def upsert(self, collection: str, id: int, vector: list[float], payload: dict) -> None: ...

class IEmbeddingEncoder(ABC):
    def encode(self, text: str) -> list[float]: ...

class IEmotionExtractor(ABC):
    def extract(self, texts: list[str]) -> EmotionVector: ...

class IMovieMetadataClient(ABC):
    async def get_poster_url(self, tmdb_id: int) -> str | None: ...
    async def get_trailer_key(self, tmdb_id: int) -> str | None: ...
```
