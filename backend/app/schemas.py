import datetime as dt

from pydantic import BaseModel, ConfigDict


class StreamStatus(BaseModel):
    id: int
    name: str
    kind: str
    priority: int | None  # None = healthy, 1/2/3 = active fault priority
    reason: str | None
    metrics: dict


class MetricPoint(BaseModel):
    timestamp: dt.datetime
    metrics: dict


class FaultOut(BaseModel):
    id: int
    stream_id: int
    stream_name: str
    timestamp: dt.datetime
    priority: int
    category: str
    reason: str
    resolved: bool

    model_config = ConfigDict(from_attributes=True)


class InjectFaultRequest(BaseModel):
    stream_name: str
    fault_type: str  # "packet_loss" | "jitter" | "dropout" | "ptp_drift" | "ptp_rogue_master"
    duration_seconds: int = 15
