# Entry point: initializes and runs the FastAPI app for StormSense AI

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="StormSense AI",
    description="Real-Time Natural Disaster Intelligence Platform",
    version="1.0.0",
)

# Allow all origins/methods/headers so the Next.js frontend (or any client) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all endpoints defined in api/routes.py
app.include_router(router)


@app.get("/")
def root():
    """Root endpoint pointing clients to the interactive API docs."""
    return {"message": "Welcome to StormSense AI", "docs": "/docs"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
