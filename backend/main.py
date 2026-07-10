# Entry point: initializes and runs the FastAPI app for StormSense AI

import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.websocket import router as websocket_router
from services.scheduler import autonomous_monitor_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the autonomous background monitor alongside the API server, so
    # StormSense keeps watching even when nobody is actively asking it anything
    monitor_task = asyncio.create_task(autonomous_monitor_loop())
    yield
    monitor_task.cancel()


app = FastAPI(
    title="StormSense AI",
    description="Real-Time Natural Disaster Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow all origins/methods/headers so the Next.js frontend (or any client) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all endpoints defined in api/routes.py and api/websocket.py
app.include_router(router)
app.include_router(websocket_router)


@app.get("/")
def root():
    """Root endpoint pointing clients to the interactive API docs."""
    return {"message": "Welcome to StormSense AI", "docs": "/docs"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
