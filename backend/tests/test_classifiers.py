import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.detection.media_classifier import classify_media
from app.detection.ptp_classifier import classify_ptp


def test_media_healthy_stream_has_no_priority():
    result = classify_media({"packet_loss_pct": 0.0, "jitter_ms": 1.0, "seq_discontinuities": 0})
    assert result.priority is None


def test_media_high_packet_loss_is_priority_1():
    result = classify_media({"packet_loss_pct": 8.0, "jitter_ms": 1.0, "seq_discontinuities": 0})
    assert result.priority == 1


def test_media_sequence_discontinuities_are_priority_1():
    result = classify_media({"packet_loss_pct": 0.0, "jitter_ms": 1.0, "seq_discontinuities": 5})
    assert result.priority == 1


def test_media_moderate_packet_loss_is_priority_2():
    result = classify_media({"packet_loss_pct": 1.5, "jitter_ms": 1.0, "seq_discontinuities": 0})
    assert result.priority == 2


def test_media_high_jitter_is_priority_2():
    result = classify_media({"packet_loss_pct": 0.0, "jitter_ms": 7.0, "seq_discontinuities": 0})
    assert result.priority == 2


def test_media_mild_jitter_is_priority_3():
    result = classify_media({"packet_loss_pct": 0.0, "jitter_ms": 3.0, "seq_discontinuities": 0})
    assert result.priority == 3


def test_ptp_locked_device_is_healthy():
    result = classify_ptp({"ptp_offset_us": 10.0, "ptp_mean_path_delay_us": 80.0, "rogue_master_detected": False})
    assert result.priority is None


def test_ptp_large_offset_is_priority_1():
    result = classify_ptp({"ptp_offset_us": 1500.0, "ptp_mean_path_delay_us": 80.0, "rogue_master_detected": False})
    assert result.priority == 1


def test_ptp_rogue_master_is_always_priority_1():
    result = classify_ptp({"ptp_offset_us": 5.0, "ptp_mean_path_delay_us": 80.0, "rogue_master_detected": True})
    assert result.priority == 1


def test_ptp_moderate_drift_is_priority_2():
    result = classify_ptp({"ptp_offset_us": 200.0, "ptp_mean_path_delay_us": 80.0, "rogue_master_detected": False})
    assert result.priority == 2


def test_ptp_high_path_delay_is_priority_2():
    result = classify_ptp({"ptp_offset_us": 10.0, "ptp_mean_path_delay_us": 600.0, "rogue_master_detected": False})
    assert result.priority == 2
