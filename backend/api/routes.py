# API routes: defines FastAPI endpoints for triggering the disaster intelligence workflow

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from graph.workflow import run_pipeline

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request body for POST /api/analyze."""

    query: str
    location: str = ""


class AnalyzeResponse(BaseModel):
    """Response body returned by POST /api/analyze."""

    overall_risk: str
    earthquake_risk: str
    flood_risk: str
    wildfire_risk: str
    alert_triggered: bool
    alert_message: str
    final_explanation: str
    final_response: str


class HealthResponse(BaseModel):
    """Response body returned by GET /api/health."""

    status: str
    message: str


@router.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    """Run the full multi-agent pipeline for the given query/location and return the risk assessment."""
    try:
        result = run_pipeline(query=request.query, location=request.location)

        return AnalyzeResponse(
            overall_risk=result.get("overall_risk") or "",
            earthquake_risk=result.get("earthquake_risk") or "",
            flood_risk=result.get("flood_risk") or "",
            wildfire_risk=result.get("wildfire_risk") or "",
            alert_triggered=result.get("alert_triggered") or False,
            alert_message=result.get("alert_message") or "",
            final_explanation=result.get("final_explanation") or "",
            final_response=result.get("final_response") or "",
        )
    except Exception as e:
        # Raise a proper HTTP error instead of letting the pipeline crash the request
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {e}")


@router.get("/api/health", response_model=HealthResponse)
def health():
    """Simple health check endpoint to confirm the API is running."""
    return HealthResponse(status="ok", message="StormSense AI is running")
