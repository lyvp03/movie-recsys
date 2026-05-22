import pickle
from pathlib import Path
from typing import Any

from domain.interfaces.i_cf_model import ICFModel


class SurpriseSVDModel(ICFModel):
    def __init__(self, model_path: str = "data/processed/cf_model.pkl"):
        self._model_path = model_path
        self._model = self._load_model(model_path)

    def _load_model(self, path: str) -> Any:
        """Load pre-trained Surprise SVD from pickle."""
        # Return None if the file doesn't exist yet (e.g. during initialization before training)
        p = Path(path)
        if not p.exists():
            return None
            
        with open(p, "rb") as f:
            return pickle.load(f)

    def predict(self, user_id: int, movie_id: int) -> float:
        if not self._model:
            # Fallback score if model is not loaded (e.g. tests or uninitialized)
            return 0.0
            
        # Surprise predict returns a Prediction object with an `est` attribute
        prediction = self._model.predict(uid=user_id, iid=movie_id)
        return prediction.est

    def get_top_n(self, user_id: int, movie_ids: list[int], n: int) -> list[tuple[int, float]]:
        if not self._model:
            return []
            
        predictions = [(mid, self.predict(user_id, mid)) for mid in movie_ids]
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:n]
