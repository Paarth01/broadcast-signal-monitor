"""
Generates synthetic PTP (IEEE 1588 / ST 2059) telemetry for a small
grandmaster + slave topology, with injectable faults: gradual offset drift
and a rogue device wrongly claiming the master role.
"""
import random
import time
from dataclasses import dataclass, field


@dataclass
class ActiveFault:
    fault_type: str
    expires_at: float


@dataclass
class PTPDevice:
    name: str
    role: str  # "grandmaster" | "slave"
    active_fault: ActiveFault | None = field(default=None)

    def inject_fault(self, fault_type: str, duration_seconds: int) -> None:
        self.active_fault = ActiveFault(fault_type, time.time() + duration_seconds)

    def _fault_active(self) -> str | None:
        if self.active_fault and time.time() < self.active_fault.expires_at:
            return self.active_fault.fault_type
        self.active_fault = None
        return None

    def tick(self) -> dict:
        if self.role == "grandmaster":
            return {"ptp_offset_us": 0.0, "ptp_mean_path_delay_us": 0.0, "rogue_master_detected": False}

        fault = self._fault_active()
        offset = random.uniform(-20.0, 20.0)
        mean_path_delay = random.uniform(50.0, 150.0)
        rogue_master = False

        if fault == "ptp_drift":
            offset = random.uniform(150.0, 1200.0)
        elif fault == "ptp_rogue_master":
            rogue_master = True

        return {
            "ptp_offset_us": round(offset, 1),
            "ptp_mean_path_delay_us": round(mean_path_delay, 1),
            "rogue_master_detected": rogue_master,
        }


def default_devices() -> list[PTPDevice]:
    return [
        PTPDevice("ptp-grandmaster", role="grandmaster"),
        PTPDevice("ptp-slave-studio-a", role="slave"),
        PTPDevice("ptp-slave-ob-van", role="slave"),
    ]
