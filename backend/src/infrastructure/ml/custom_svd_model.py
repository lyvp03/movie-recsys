import pickle
from pathlib import Path
from typing import Any

import numpy as np
from domain.interfaces.i_cf_model import ICFModel


class MatrixFactorizationSVD:
    """
    A custom SGD Matrix Factorization model (Funk SVD with biases).
    Written because scikit-surprise is incompatible with Python 3.13.
    """
    def __init__(self, n_factors=100, n_epochs=20, lr=0.005, reg=0.02):
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr = lr
        self.reg = reg
        
        self.global_mean = 0.0
        self.bu = {}  # User biases
        self.bi = {}  # Item biases
        self.pu = {}  # User factors
        self.qi = {}  # Item factors

    def fit(self, ratings: list[tuple[int, int, float]]):
        """
        Train the model using Stochastic Gradient Descent.
        ratings: list of (user_id, movie_id, rating)
        """
        if not ratings:
            return

        # Copy to avoid mutating caller's data during shuffle
        ratings = list(ratings)

        self.global_mean = sum(r for _, _, r in ratings) / len(ratings)
        
        # Initialize biases and latent factors
        for u, i, _ in ratings:
            if u not in self.bu:
                self.bu[u] = 0.0
                self.pu[u] = np.random.normal(0, 0.1, self.n_factors)
            if i not in self.bi:
                self.bi[i] = 0.0
                self.qi[i] = np.random.normal(0, 0.1, self.n_factors)
                
        # SGD
        for epoch in range(self.n_epochs):
            np.random.shuffle(ratings)
            for u, i, r in ratings:
                # Predict
                pred = self.global_mean + self.bu[u] + self.bi[i] + np.dot(self.pu[u], self.qi[i])
                err = r - pred
                
                # Update biases
                self.bu[u] += self.lr * (err - self.reg * self.bu[u])
                self.bi[i] += self.lr * (err - self.reg * self.bi[i])
                
                # Update factors
                pu_u = self.pu[u]
                qi_i = self.qi[i]
                
                self.pu[u] += self.lr * (err * qi_i - self.reg * pu_u)
                self.qi[i] += self.lr * (err * pu_u - self.reg * qi_i)
                
    def predict(self, uid: int, iid: int) -> float:
        pred = self.global_mean
        
        if uid in self.bu:
            pred += self.bu[uid]
        if iid in self.bi:
            pred += self.bi[iid]
            
        if uid in self.pu and iid in self.qi:
            pred += np.dot(self.pu[uid], self.qi[iid])
            
        # Clip to [0.5, 5.0]
        return max(0.5, min(5.0, pred))


class CustomSVDModel(ICFModel):
    def __init__(self, model_path: str = "data/processed/cf_model.pkl"):
        self._model_path = model_path
        self._model = self._load_model(model_path)

    def _load_model(self, path: str) -> Any:
        p = Path(path)
        if not p.exists():
            return None
        with open(p, "rb") as f:
            return pickle.load(f)

    def predict(self, user_id: int, movie_id: int) -> float:
        if not self._model:
            return 0.0
        return self._model.predict(uid=user_id, iid=movie_id)

    def get_top_n(self, user_id: int, movie_ids: list[int], n: int) -> list[tuple[int, float]]:
        if not self._model:
            return []
            
        predictions = [(mid, self.predict(user_id, mid)) for mid in movie_ids]
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:n]
