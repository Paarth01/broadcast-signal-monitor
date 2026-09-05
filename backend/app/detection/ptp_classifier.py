"""
Classifies PTP (IEEE 1588 / SMPTE ST 2059) synchronization health.

Modeled as a separate category from media stream health because that's how
real ST 2110 monitoring systems treat it: PTP offset, mean path delay, and
master-election state are tracked per grandmaster/master/slave device,
independently of the media essence streams that depend on that timing.
"""
from dataclasses import dataclass

from app.config import (
    PTP_MEAN_PATH_DELAY_WARN_US,
    PTP_P1_OFFSET_US,
    PTP_P2_OFFSET_US,
    PTP_P3_OFFSET_US,
)


@dataclass
class ClassificationResult:
    priority: int | None
    reason: str | None


def classify_ptp(metrics: dict) -> ClassificationResult:
    offset = abs(metrics.get("ptp_offset_us", 0.0))
    mean_path_delay = metrics.get("ptp_mean_path_delay_us", 0.0)
    rogue_master = metrics.get("rogue_master_detected", False)

    if rogue_master:
        return ClassificationResult(1, "Unexpected device advertising itself as PTP master (rogue master)")

    if offset >= PTP_P1_OFFSET_US:
        return ClassificationResult(1, f"PTP offset {offset:.0f} us — sync effectively lost")
    if offset >= PTP_P2_OFFSET_US:
        return ClassificationResult(2, f"PTP offset {offset:.0f} us — drifting, still locked")
    if mean_path_delay >= PTP_MEAN_PATH_DELAY_WARN_US:
        return ClassificationResult(2, f"Mean path delay {mean_path_delay:.0f} us above expected network delay")
    if offset >= PTP_P3_OFFSET_US:
        return ClassificationResult(3, f"PTP offset {offset:.0f} us trending upward")

    return ClassificationResult(None, None)
