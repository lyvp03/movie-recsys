from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

from domain.exceptions import DomainError


class TFIDFVectorizerWrapper:
    """Wrapper for sklearn TfidfVectorizer to provide a clean domain interface."""

    def __init__(self, max_features: int = 5000):
        self._vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words="english",
            ngram_range=(1, 2),
        )
        self._is_fitted = False

    def fit(self, texts: list[str]) -> None:
        """Fit the TF-IDF model on a list of texts."""
        self._vectorizer.fit(texts)
        self._is_fitted = True

    def transform(self, texts: list[str]) -> list[list[float]]:
        """Transform a list of texts into dense vectors."""
        if not self._is_fitted:
            raise DomainError("Vectorizer has not been fitted yet")
        
        # transform returns a sparse matrix. toarray() converts it to a dense numpy array
        sparse_matrix = self._vectorizer.transform(texts)
        dense_array = sparse_matrix.toarray()
        
        # Convert numpy floats to python native floats
        return [list(map(float, row)) for row in dense_array]

    def save(self, path: Path) -> None:
        """Save the fitted model to disk using joblib."""
        if not self._is_fitted:
            raise DomainError("Cannot save unfitted vectorizer")
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._vectorizer, path)

    def load(self, path: Path) -> None:
        """Load a fitted model from disk."""
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        self._vectorizer = joblib.load(path)
        self._is_fitted = True

    def get_feature_dim(self) -> int:
        """Return the dimensionality of the vectors."""
        if not self._is_fitted:
            raise DomainError("Vectorizer has not been fitted yet")
        return len(self._vectorizer.get_feature_names_out())
