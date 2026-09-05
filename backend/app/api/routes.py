from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import state_store
from app.database import get_db
from app.models import FaultEvent, MetricLog, Stream
from app.schemas import FaultOut, InjectFaultRequest, MetricPoint, StreamStatus
from app.simulator.engine import inject_fault

router = APIRouter(prefix="/api")


@router.get("/streams", response_model=list[StreamStatus])
def list_streams(db: Session = Depends(get_db)):
    statuses = {s["name"]: s for s in state_store.all_statuses()}
    out = []
    for row in db.query(Stream).all():
        live = statuses.get(row.name, {})
        out.append(
            StreamStatus(
                id=row.id,
                name=row.name,
                kind=row.kind,
                priority=live.get("priority"),
                reason=live.get("reason"),
                metrics=live.get("metrics", {}),
            )
        )
    return out


@router.get("/streams/{name}", response_model=StreamStatus)
def get_stream(name: str, db: Session = Depends(get_db)):
    row = db.query(Stream).filter_by(name=name).first()
    if not row:
        raise HTTPException(status_code=404, detail="Stream not found")
    live = state_store.get_status(name) or {}
    return StreamStatus(
        id=row.id,
        name=row.name,
        kind=row.kind,
        priority=live.get("priority"),
        reason=live.get("reason"),
        metrics=live.get("metrics", {}),
    )


@router.get("/streams/{name}/history", response_model=list[MetricPoint])
def get_stream_history(name: str, limit: int = 40, db: Session = Depends(get_db)):
    """Recent persisted metric points for a stream, oldest first - lets the
    frontend chart show trend history immediately on load or when switching
    streams, rather than only what's accumulated during the current
    browser session from the live SSE feed."""
    row = db.query(Stream).filter_by(name=name).first()
    if not row:
        raise HTTPException(status_code=404, detail="Stream not found")

    rows = (
        db.query(MetricLog)
        .filter_by(stream_id=row.id)
        .order_by(MetricLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()  # oldest first, matching chart's left-to-right time axis

    return [
        MetricPoint(
            timestamp=m.timestamp,
            metrics={
                k: v
                for k, v in {
                    "bitrate_mbps": m.bitrate_mbps,
                    "jitter_ms": m.jitter_ms,
                    "packet_loss_pct": m.packet_loss_pct,
                    "seq_discontinuities": m.seq_discontinuities,
                    "ptp_offset_us": m.ptp_offset_us,
                    "ptp_mean_path_delay_us": m.ptp_mean_path_delay_us,
                }.items()
                if v is not None
            },
        )
        for m in rows
    ]


@router.get("/faults", response_model=list[FaultOut])
def list_faults(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(FaultEvent).order_by(FaultEvent.timestamp.desc()).limit(limit).all()
    return [
        FaultOut(
            id=f.id,
            stream_id=f.stream_id,
            stream_name=f.stream.name,
            timestamp=f.timestamp,
            priority=f.priority,
            category=f.category,
            reason=f.reason,
            resolved=bool(f.resolved),
        )
        for f in rows
    ]


@router.post("/simulate/fault")
def simulate_fault(req: InjectFaultRequest):
    ok = inject_fault(req.stream_name, req.fault_type, req.duration_seconds)
    if not ok:
        raise HTTPException(status_code=404, detail="Unknown stream name")
    return {"status": "fault injected", "stream_name": req.stream_name, "fault_type": req.fault_type}
