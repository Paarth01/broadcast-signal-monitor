"""
Holds the current live status of every stream/device so API reads are fast
and don't hit Postgres on every poll. Uses Redis when REDIS_URL is set
(docker-compose stack); otherwise falls back to an in-process dict so the
backend runs standalone with zero external services.
"""
import json
import threading

from app.config import REDIS_URL

_lock = threading.Lock()
_memory_store: dict[str, str] = {}

_redis_client = None
if REDIS_URL:
    import redis  # imported lazily so redis isn't required for the fallback path
    _redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def set_status(name: str, payload: dict) -> None:
    value = json.dumps(payload)
    if _redis_client:
        _redis_client.set(f"stream:{name}", value)
    else:
        with _lock:
            _memory_store[f"stream:{name}"] = value


def get_status(name: str) -> dict | None:
    if _redis_client:
        raw = _redis_client.get(f"stream:{name}")
    else:
        with _lock:
            raw = _memory_store.get(f"stream:{name}")
    return json.loads(raw) if raw else None


def all_statuses() -> list[dict]:
    if _redis_client:
        keys = _redis_client.keys("stream:*")
        return [json.loads(_redis_client.get(k)) for k in keys]
    with _lock:
        return [json.loads(v) for v in _memory_store.values()]
