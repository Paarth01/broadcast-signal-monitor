import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.sse import router as sse_router
from app.database import init_db
from app.simulator.engine import run_forever


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    simulator_task = asyncio.create_task(run_forever())
    try:
        yield
    finally:
        simulator_task.cancel()


app = FastAPI(title="IP Broadcast Signal Health Monitor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(sse_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

