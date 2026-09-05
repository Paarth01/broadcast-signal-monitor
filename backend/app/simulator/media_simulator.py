"""
Generates synthetic per-stream telemetry standing in for real RTP/ST 2110
essence flow measurements (bitrate, jitter, packet loss, sequence
discontinuities). Faults can be injected on demand to demo the detection
pipeline without needing real broadcast hardware.
"""
import random
import time
from dataclasses import dataclass, field


@dataclass
class ActiveFault:
    fault_type: str
    expires_at: float


@dataclass
class MediaStream:
    name: str
    base_bitrate_mbps: float
    active_fault: ActiveFault | None = field(default=None)

    def inject_fault(self, fault_type: str, duration_seconds: int) -> None:
        self.active_fault = ActiveFault(fault_type, time.time() + duration_seconds)

    def _fault_active(self) -> str | None:
        if self.active_fault and time.time() < self.active_fault.expires_at:
            return self.active_fault.fault_type
        self.active_fault = None
        return None

    def tick(self) -> dict:
        fault = self._fault_active()

        bitrate = self.base_bitrate_mbps + random.uniform(-0.3, 0.3)
        jitter = random.uniform(0.5, 1.8)
        packet_loss = 0.0
        seq_discontinuities = 0

        if fault == "packet_loss":
            packet_loss = random.uniform(1.5, 3.0)
        elif fault == "jitter":
            jitter = random.uniform(6.0, 12.0)
        elif fault == "dropout":
            bitrate *= 0.1
            packet_loss = random.uniform(6.0, 10.0)
            seq_discontinuities = random.randint(3, 6)
        elif fault == "soft_drift":
            # Deliberately stays just under every rule threshold at once
            # (P2 packet loss 1.0%, P3 jitter 2.0ms) - a combination the
            # fixed-threshold classifier can never catch by construction.
            # This is what the ML anomaly layer exists to catch.
            jitter = random.uniform(1.5, 1.95)
            packet_loss = random.uniform(0.4, 0.95)

        return {
            "bitrate_mbps": round(bitrate, 2),
            "jitter_ms": round(jitter, 2),
            "packet_loss_pct": round(packet_loss, 2),
            "seq_discontinuities": seq_discontinuities,
        }


def default_streams() -> list[MediaStream]:
    return [
        MediaStream("camera-1-studio-a", base_bitrate_mbps=24.0),
        MediaStream("camera-2-studio-a", base_bitrate_mbps=24.0),
        MediaStream("ob-van-uplink", base_bitrate_mbps=20.0),
        MediaStream("satellite-feed", base_bitrate_mbps=18.0),
        MediaStream("backup-encoder", base_bitrate_mbps=24.0),
    ]
