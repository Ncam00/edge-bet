"""
XGBoost model: train, calibrate, predict.

Training data: historical NBA games (2021-24 seasons)
Target: home_win (binary 0/1)
Output: calibrated probability via Platt scaling
"""
import pickle
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss, accuracy_score
import xgboost as xgb
from app.ml.features import features_to_array, FEATURE_ORDER  # type: ignore

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "model.pkl"

FEATURE_ORDER = [
    "home_win_pct", "home_avg_pts", "home_avg_allowed",
    "home_home_win_pct", "home_net_rating",
    "away_win_pct", "away_avg_pts", "away_avg_allowed",
    "away_away_win_pct", "away_net_rating",
    "win_pct_diff", "net_rating_diff",
    "h2h_home_win_pct", "h2h_games",
]


class EdgeBetModel:
    """Wrapper around XGBoost + Platt calibration."""

    def __init__(self):
        self.model = None
        self._load()

    def _load(self):
        if MODEL_PATH.exists():
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            logger.info("Model loaded from disk")
        else:
            logger.warning("No trained model found — run train() first")

    def train(self, df: pd.DataFrame) -> dict:
        """
        Train on a DataFrame with feature columns + 'home_win' label.
        Returns evaluation metrics.
        """
        X = df[FEATURE_ORDER].values
        y = df["home_win"].values

        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

        base_model = xgb.XGBClassifier(
            max_depth=4,
            n_estimators=200,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            use_label_encoder=False,
            random_state=42,
        )

        calibrated = CalibratedClassifierCV(base_model, cv=5, method="sigmoid")
        calibrated.fit(X_train, y_train)

        probs = calibrated.predict_proba(X_val)[:, 1]
        preds = (probs >= 0.5).astype(int)

        metrics = {
            "accuracy": round(accuracy_score(y_val, preds), 4),
            "log_loss": round(log_loss(y_val, probs), 4),
            "val_samples": len(y_val),
        }

        self.model = calibrated
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(calibrated, f)

        logger.info(f"Model trained: {metrics}")
        return metrics

    def predict_proba(self, features: dict) -> float | None:
        """
        Given a feature dict, return P(home_win) as float 0-1.
        Returns None if model not loaded.
        """
        if self.model is None:
            logger.error("Model not loaded")
            return None

        feature_array = np.array(features_to_array(features)).reshape(1, -1)
        prob = self.model.predict_proba(feature_array)[0][1]
        return round(float(prob), 4)

    def is_ready(self) -> bool:
        return self.model is not None


# Singleton
_model_instance = None


def get_model() -> EdgeBetModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = EdgeBetModel()
    return _model_instance
