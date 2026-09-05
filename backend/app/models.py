import datetime as dt


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    kind = Column(String, default="media")  # media | ptp_device

    metrics = relationship("MetricLog", back_populates="stream")
    faults = relationship("FaultEvent", back_populates="stream")


class MetricLog(Base):
    __tablename__ = "metrics_log"

    id = Column(Integer, primary_key=True)
    stream_id = Column(Integer, ForeignKey("streams.id"), nullable=False)
    timestamp = Column(DateTime, default=utcnow)

    # Media metrics (null for PTP devices)
    bitrate_mbps = Column(Float, nullable=True)
    jitter_ms = Column(Float, nullable=True)
    packet_loss_pct = Column(Float, nullable=True)
    seq_discontinuities = Column(Integer, nullable=True)

    # PTP metrics (null for media streams)
    ptp_offset_us = Column(Float, nullable=True)
    ptp_mean_path_delay_us = Column(Float, nullable=True)

    stream = relationship("Stream", back_populates="metrics")


class FaultEvent(Base):
    __tablename__ = "fault_events"

    id = Column(Integer, primary_key=True)
    stream_id = Column(Integer, ForeignKey("streams.id"), nullable=False)
    timestamp = Column(DateTime, default=utcnow)
    priority = Column(Integer, nullable=False)  # 1, 2, or 3
    category = Column(String, nullable=False)   # "media" | "ptp"
    reason = Column(String, nullable=False)
    resolved = Column(Integer, default=0)  # 0/1 boolean (sqlite-friendly)

    stream = relationship("Stream", back_populates="faults")
