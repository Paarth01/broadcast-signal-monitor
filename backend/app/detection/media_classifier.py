"""
Classifies media stream telemetry into a TR 101 290-style priority.

Real DVB/broadcast monitoring equipment grades stream errors into three
priorities (ETSI TR 101 290):
  Priority 1 - breaks decodability (e.g. sync loss, continuity errors)
  Priority 2 - impairs quality, may cause visible artifacts
  Priority 3 - informational / application-dependent, doesn't affect
               decodability

We don't parse real MPEG-TS/RTP headers here (there's no real transport
stream — this is a simulated environment), but we deliberately mirror the
three-tier severity model and reasoning structure, because that's the
mental model a broadcast engineer actually uses when triaging a stream.
"""
from dataclasses import dataclass

from app.config import (
    MEDIA_P1_PACKET_LOSS_PCT,
    MEDIA_P1_SEQ_DISCONTINUITY_COUNT,
    MEDIA_P2_JITTER_MS,
    MEDIA_P2_PACKET_LOSS_PCT,
    MEDIA_P3_JITTER_MS,
)
from app.ml.model import score_media


@dataclass
class ClassificationResult:
    priority: int | None  # None = healthy
    reason: str | None
    source: str = "rule"  # "rule" | "ml" - which layer raised this


def classify_media(metrics: dict) -> ClassificationResult:
    packet_loss = metrics.get("packet_loss_pct", 0.0)
    jitter = metrics.get("jitter_ms", 0.0)
    seq_discontinuities = metrics.get("seq_discontinuities", 0)

    # Priority 1: decodability is broken or about to be.
    if packet_loss >= MEDIA_P1_PACKET_LOSS_PCT:
        return ClassificationResult(1, f"Packet loss {packet_loss:.1f}% exceeds decodability threshold")
    if seq_discontinuities >= MEDIA_P1_SEQ_DISCONTINUITY_COUNT:
        return ClassificationResult(
            1, f"{seq_discontinuities} sequence discontinuities in window (continuity count failure)"
        )

    # Priority 2: quality-impairing, still decodable.
    if packet_loss >= MEDIA_P2_PACKET_LOSS_PCT:
        return ClassificationResult(2, f"Packet loss {packet_loss:.1f}% likely to cause visible artifacts")
    if jitter >= MEDIA_P2_JITTER_MS:
        return ClassificationResult(2, f"Jitter {jitter:.1f} ms above stable-playout threshold")

    # Priority 3: informational drift worth logging, not yet impairing.
    if jitter >= MEDIA_P3_JITTER_MS:
        return ClassificationResult(3, f"Jitter {jitter:.1f} ms trending upward")

    # Nothing crossed a fixed threshold — ask the anomaly detector whether
    # this combination of metrics still looks like drift the thresholds
    # haven't caught up to yet (e.g. jitter and packet loss both mildly
    # elevated at once, neither alone enough to trip a rule).
    is_anomaly, score = score_media(metrics)
    if is_anomaly:
        return ClassificationResult(3, f"ML anomaly detector flagged drift (score={score:.2f})", source="ml")

    return ClassificationResult(None, None)
