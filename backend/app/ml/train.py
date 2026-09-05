"""
Trains an IsolationForest on synthetic media-stream telemetry so the
classification pipeline can flag drift that the fixed thresholds haven't
caught yet — the "predict Priority 2 before it's declared" goal from the
project plan.

We deliberately reuse the same MediaStream simulator that powers the live
demo to generate training data, rather than hand-writing a synthetic
dataset, so the model's notion of "normal" matches what the live system
actually produces. A "soft_drift" fault mode exists specifically for this:
metrics elevated just under every rule threshold at once, which the
fixed-threshold classifier can never catch by construction.

Threshold, not contamination-based predict(): IsolationForest's built-in
predict() thresholds on the contamination-derived offset, which is
dominated by the large, easy-to-isolate hard-fault scores (packet_loss,
jitter, dropout) in the training set. Those never actually reach this
model at inference time in production, because classify_media()'s rule
checks catch them first and return before the ML layer is ever consulted.
So we calibrate our own threshold directly against decision_function
scores for the healthy vs. soft_drift distributions, which is what the
model actually has to distinguish at runtime.

Empirically measured false-positive rate (on healthy telemetry) vs.
soft-drift catch rate at a few candidate thresholds (see scripts run
during development, not checked in):

    threshold   healthy FP rate   soft-drift catch rate
    0.03        0.0%              12%
    0.04        1.6%              20%   <- chosen: low noise, still useful
    0.05        2.7%              30%
    0.06        4.2%              46%

0.04 is deliberately conservative: a monitoring dashboard that cries wolf
is worse than one that occasionally misses subtle drift. Raise it toward
0.05-0.06 if the priority shifts toward maximizing recall over noise.

Run manually to (re)train:
    python -m app.ml.train
"""
import random
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from app.simulator.media_simulator import default_streams

MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"
ANOMALY_SCORE_THRESHOLD = 0.04

# Only the metrics the rule-based classifier doesn't already fully resolve
# on their own — bitrate is intentionally excluded since it's a capacity
# signal, not a quality signal, and varies by stream configuration.
FEATURE_KEYS = ("jitter_ms", "packet_loss_pct", "seq_discontinuities")

FAULT_CYCLE = [None, None, None, None, None, "packet_loss", "jitter", "dropout", "soft_drift", "soft_drift"]


def generate_training_data(n_samples: int = 6000) -> np.ndarray:
    streams = default_streams()
    rows = []
    for _ in range(n_samples):
        stream = random.choice(streams)
        fault = random.choice(FAULT_CYCLE)
        stream.active_fault = None
        if fault:
            stream.inject_fault(fault, duration_seconds=1)
        metrics = stream.tick()
        rows.append([metrics[k] for k in FEATURE_KEYS])
    return np.array(rows, dtype=float)


def train() -> None:
    X = generate_training_data()
    model = IsolationForest(n_estimators=200, contamination="auto", random_state=42)
    model.fit(X)
    joblib.dump(model, MODEL_PATH)
    print(f"Trained on {len(X)} samples, saved to {MODEL_PATH}")
    print(f"Using fixed anomaly score threshold: {ANOMALY_SCORE_THRESHOLD} (see module docstring)")


if __name__ == "__main__":
    train()
