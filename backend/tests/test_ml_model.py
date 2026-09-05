from app.ml.model import score_media


def test_clean_normal_tick_is_not_flagged():
    is_anomaly, _ = score_media({"jitter_ms": 1.0, "packet_loss_pct": 0.0, "seq_discontinuities": 0})
    assert is_anomaly is False


def test_extreme_outlier_is_flagged():
    # Far outside anything the simulator produces in normal or single-fault
    # states — should be unambiguously anomalous regardless of model seed.
    is_anomaly, score = score_media({"jitter_ms": 80.0, "packet_loss_pct": 95.0, "seq_discontinuities": 40})
    assert is_anomaly is True
    assert score < 0


def test_soft_drift_is_flagged_more_often_than_healthy_telemetry():
    # The threshold is deliberately conservative (see app/ml/train.py), so
    # soft_drift isn't caught every time — but it should be caught
    # meaningfully more often than genuinely healthy telemetry is.
    import random

    from app.simulator.media_simulator import default_streams

    random.seed(123)
    streams = default_streams()

    def flag_rate(fault, n=300):
        hits = 0
        for _ in range(n):
            s = random.choice(streams)
            s.active_fault = None
            if fault:
                s.inject_fault(fault, duration_seconds=1)
            is_anomaly, _ = score_media(s.tick())
            hits += is_anomaly
        return hits / n

    healthy_rate = flag_rate(None)
    drift_rate = flag_rate("soft_drift")

    assert healthy_rate < 0.03  # near-zero false positives on healthy telemetry
    assert drift_rate > healthy_rate * 3  # meaningfully more sensitive to real drift


def test_missing_model_degrades_gracefully(monkeypatch):
    import app.ml.model as model_module

    monkeypatch.setattr(model_module, "_model", None)
    monkeypatch.setattr(model_module, "_load_attempted", True)  # pretend we already tried and found nothing

    is_anomaly, score = score_media({"jitter_ms": 1.0, "packet_loss_pct": 0.0, "seq_discontinuities": 0})
    assert is_anomaly is False
    assert score == 0.0
