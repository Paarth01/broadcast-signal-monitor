import asyncio
import datetime as dt

from app import state_store
from app.config import SIMULATOR_TICK_SECONDS
from app.database import SessionLocal
from app.detection.media_classifier import classify_media
from app.detection.ptp_classifier import classify_ptp
from app.models import FaultEvent, MetricLog, Stream
from app.simulator.media_simulator import default_streams
from app.simulator.ptp_simulator import default_devices

_media_streams = {s.name: s for s in default_streams()}
_ptp_devices = {d.name: d for d in default_devices()}

# One asyncio.Queue per connected SSE client; engine broadcasts to all of them.
_subscribers: set[asyncio.Queue] = set()

# Tracks whether a stream currently has an open (unresolved) fault, so we
# only write a new FaultEvent row when the priority changes rather than
# every tick.
_open_fault_priority: dict[str, int | None] = {}


def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=50)
    _subscribers.add(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    _subscribers.discard(q)


def inject_fault(stream_name: str, fault_type: str, duration_seconds: int) -> bool:
    if stream_name in _media_streams:
        _media_streams[stream_name].inject_fault(fault_type, duration_seconds)
        return True
    if stream_name in _ptp_devices:
        _ptp_devices[stream_name].inject_fault(fault_type, duration_seconds)
        return True
    return False


def _get_or_create_stream_row(db, name: str, kind: str) -> Stream:
    row = db.query(Stream).filter_by(name=name).first()
    if row is None:
        row = Stream(name=name, kind=kind)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


async def _broadcast(payload: dict) -> None:
    for q in list(_subscribers):
        if q.full():
            _ = q.get_nowait()  # drop oldest rather than block a slow client
        await q.put(payload)


async def run_forever() -> None:
    db = SessionLocal()
    for name in list(_media_streams) + list(_ptp_devices):
        kind = "media" if name in _media_streams else "ptp_device"
        _get_or_create_stream_row(db, name, kind)
    db.close()

    while True:
        db = SessionLocal()
        try:
            for name, stream in _media_streams.items():
                metrics = stream.tick()
                result = classify_media(metrics)
                await _handle_tick(db, name, "media", metrics, result.priority, result.reason)

            for name, device in _ptp_devices.items():
                metrics = device.tick()
                result = classify_ptp(metrics)
                await _handle_tick(db, name, "ptp", metrics, result.priority, result.reason)

            # Commit every tick: each tick uses its own short-lived session,
            # so anything left uncommitted here is silently lost on db.close().
            db.commit()
        finally:
            db.close()

        await asyncio.sleep(SIMULATOR_TICK_SECONDS)


async def _handle_tick(db, name, category, metrics, priority, reason) -> None:
    row = db.query(Stream).filter_by(name=name).first()

    payload = {
        "name": name,
        "category": category,
        "priority": priority,
        "reason": reason,
        "metrics": metrics,
        "timestamp": dt.datetime.now(dt.UTC).isoformat(),
    }
    state_store.set_status(name, payload)
    await _broadcast(payload)

    metric_log = MetricLog(
        stream_id=row.id,
        bitrate_mbps=metrics.get("bitrate_mbps"),
        jitter_ms=metrics.get("jitter_ms"),
        packet_loss_pct=metrics.get("packet_loss_pct"),
        seq_discontinuities=metrics.get("seq_discontinuities"),
        ptp_offset_us=metrics.get("ptp_offset_us"),
        ptp_mean_path_delay_us=metrics.get("ptp_mean_path_delay_us"),
    )
    db.add(metric_log)

    previous_priority = _open_fault_priority.get(name)
    if priority != previous_priority:
        _open_fault_priority[name] = priority
        if priority is not None:
            db.add(FaultEvent(stream_id=row.id, priority=priority, category=category, reason=reason))
        else:
            # Recovered to healthy - close out any fault rows still marked
            # open for this stream, so `resolved` actually reflects reality
            # instead of staying permanently false.
            db.query(FaultEvent).filter_by(stream_id=row.id, resolved=0).update({"resolved": 1})
