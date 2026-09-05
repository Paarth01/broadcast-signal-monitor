import asyncio
import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.simulator.engine import subscribe, unsubscribe

router = APIRouter(prefix="/api")


@router.get("/stream/events")
async def stream_events():
    queue = subscribe()

    async def event_generator():
        try:
            while True:
                payload = await queue.get()
                yield {"event": "status", "data": json.dumps(payload)}
        except asyncio.CancelledError:
            pass
        finally:
            unsubscribe(queue)

    return EventSourceResponse(event_generator())
