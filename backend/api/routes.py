# API routes: defines FastAPI endpoints for triggering the disaster intelligence workflow

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.analysis_agent import classify_earthquake_magnitude
from graph.workflow import run_pipeline
from tools.firms_tool import parse_wildfire_data
from tools.usgs_tool import parse_earthquake_data
from tools.weather_tool import parse_weather_data

router = APIRouter()

# Caps keep the dashboard/map payload light — USGS is already limited to 10
# events by the Data Agent's fetch params, but FIRMS can return thousands of
# wildfire hotspots, so only the most intense ones are surfaced as markers.
MAX_WILDFIRE_MARKERS = 8


class AnalyzeRequest(BaseModel):
    """Request body for POST /api/analyze."""

    query: str
    location: str = ""


class DisasterEvent(BaseModel):
    """A single real disaster event, shaped for the frontend's map/dashboard."""

    id: str
    type: str  # "earthquake" | "flood" | "wildfire"
    location: str
    magnitude: Optional[float] = None
    severity: Optional[str] = None
    lat: float
    lng: float
    risk: str
    time: str
    description: str


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
    events: List[DisasterEvent]


class HealthResponse(BaseModel):
    """Response body returned by GET /api/health."""

    status: str
    message: str


def _format_time(iso_timestamp: Optional[str]) -> str:
    """Turn an ISO-8601 timestamp into a short display string, or '' if missing."""
    if not iso_timestamp:
        return ""
    return iso_timestamp[:16].replace("T", " ")


def _build_earthquake_events(raw_earthquake_data: Optional[dict]) -> List[DisasterEvent]:
    """Convert raw USGS data into map-ready earthquake events with per-event risk."""
    parsed = parse_earthquake_data(raw_earthquake_data or {})
    events: List[DisasterEvent] = []

    for quake in parsed:
        coords = quake.get("coordinates") or {}
        lat, lng = coords.get("latitude"), coords.get("longitude")
        magnitude = quake.get("magnitude")
        if lat is None or lng is None or magnitude is None:
            continue

        events.append(
            DisasterEvent(
                id=f"eq-{quake.get('event_id')}",
                type="earthquake",
                location=quake.get("location") or "Unknown location",
                magnitude=magnitude,
                lat=lat,
                lng=lng,
                risk=classify_earthquake_magnitude(magnitude),
                time=_format_time(quake.get("time")),
                description=(
                    f"Magnitude {magnitude} earthquake detected "
                    f"at a depth of {quake.get('depth_km')} km."
                ),
            )
        )

    return events


def _build_wildfire_events(raw_wildfire_data: Optional[dict], wildfire_risk: str) -> List[DisasterEvent]:
    """Convert raw NASA FIRMS hotspots into the most intense map-ready wildfire markers."""
    hotspots = (raw_wildfire_data or {}).get("hotspots", [])
    parsed = parse_wildfire_data(hotspots)

    with_coords = [
        h for h in parsed
        if (h.get("coordinates") or {}).get("latitude") is not None
        and (h.get("coordinates") or {}).get("longitude") is not None
    ]
    with_coords.sort(key=lambda h: h.get("frp") or 0, reverse=True)

    events: List[DisasterEvent] = []
    for idx, hotspot in enumerate(with_coords[:MAX_WILDFIRE_MARKERS]):
        coords = hotspot["coordinates"]
        events.append(
            DisasterEvent(
                id=f"wf-{idx}-{coords['latitude']}-{coords['longitude']}",
                type="wildfire",
                location=hotspot.get("location") or "Unknown location",
                severity=wildfire_risk,
                lat=coords["latitude"],
                lng=coords["longitude"],
                risk=wildfire_risk,
                time=_format_time(hotspot.get("detected_at")),
                description=(
                    f"Active fire hotspot (fire radiative power: {hotspot.get('frp')} MW, "
                    f"confidence: {hotspot.get('confidence')})."
                ),
            )
        )

    return events


def _build_weather_events(raw_weather_data: Optional[dict]) -> List[DisasterEvent]:
    """Convert raw OpenWeatherMap data into map-ready flood/storm events."""
    parsed = parse_weather_data(raw_weather_data or {})
    events: List[DisasterEvent] = []

    for idx, item in enumerate(parsed):
        if item.get("type") not in ("flood", "storm"):
            continue

        coords = item.get("coordinates") or {}
        lat, lng = coords.get("latitude"), coords.get("longitude")
        if lat is None or lng is None:
            continue

        events.append(
            DisasterEvent(
                id=f"wx-{idx}",
                type="flood",
                location=item.get("area") or "Unknown location",
                severity=item.get("severity"),
                lat=lat,
                lng=lng,
                risk=item.get("severity") or "Low",
                time=_format_time(item.get("issued_at")),
                description=item.get("description") or item.get("event_name") or "Weather event detected.",
            )
        )

    return events


def build_dashboard_events(result: dict) -> List[DisasterEvent]:
    """Assemble the full list of real, map-ready disaster events from a pipeline run's raw data."""
    events = []
    events.extend(_build_earthquake_events(result.get("raw_earthquake_data")))
    events.extend(_build_weather_events(result.get("raw_weather_data")))
    events.extend(_build_wildfire_events(result.get("raw_wildfire_data"), result.get("wildfire_risk") or "Low"))
    return events


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
            events=build_dashboard_events(result),
        )
    except Exception as e:
        # Raise a proper HTTP error instead of letting the pipeline crash the request
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {e}")


@router.get("/api/health", response_model=HealthResponse)
def health():
    """Simple health check endpoint to confirm the API is running."""
    return HealthResponse(status="ok", message="StormSense AI is running")
