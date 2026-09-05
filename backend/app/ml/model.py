"""
Lazy-loads the trained anomaly model and scores incoming media telemetry.
If no model has been trained yet (model.joblib absent), scoring is a no-op
so the rest of the pipeline degrades gracefully to rule-based-only.

Uses a fixed, empirically calibrated score threshold rather than the
model's own contamination-based predict() — see app/ml/train.py's
docstring for why.
"""
from pathlib import Path

import joblib

from app.ml.train import ANOMALY_SCORE_THRESHOLD, FEATURE_KEYS

MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"

_model = None
_load_attempted = False


def _load():
    global _model, _load_attempted
    if not _load_attempted:
        _load_attempted = True
        if MODEL_PATH.exists():
            _model = joblib.load(MODEL_PATH)
    return _model


def score_media(metrics: dict) -> tuple[bool, float]:
    """Returns (is_anomaly, anomaly_score). Lower score = more anomalous.
    Returns (False, 0.0) if no trained model is present."""
    model = _load()
    if model is None:
        return False, 0.0

    features = [[metrics.get(k, 0.0) for k in FEATURE_KEYS]]
    score = float(model.decision_function(features)[0])
    return score < ANOMALY_SCORE_THRESHOLD, score
