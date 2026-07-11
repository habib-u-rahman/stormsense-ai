# API routes: defines FastAPI endpoints for triggering the disaster intelligence workflow

import asyncio
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.analysis_agent import classify_earthquake_magnitude
from api.websocket import broadcast
from graph.workflow import run_pipeline
from services.history import get_history
from services.simulator import SCENARIOS
from services.subscribers import add_subscriber, get_subscriber_count
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
    risk_trend: Optional[str] = None
    notification_sent: bool = False
    simulated: bool = False
    events: List[DisasterEvent]


class HealthResponse(BaseModel):
    """Response body returned by GET /api/health."""

    status: str
    message: str


class HistoryEntryResponse(BaseModel):
    """A single point-in-time risk snapshot, for the dashboard's trend chart."""

    timestamp: str
    overall_risk: str
    earthquake_risk: str
    flood_risk: str
    wildfire_risk: str


class SimulateRequest(BaseModel):
    """Request body for POST /api/simulate. Runs the real pipeline on a
    synthetic High/Critical scenario so the alert flow can be demoed without
    waiting for a real disaster."""

    scenario: str  # "earthquake" | "wildfire" | "flood"
    send_email: bool = False


class SubscribeRequest(BaseModel):
    """Request body for POST /api/subscribe. No login — just an email to alert."""

    value: str


class SubscribeResponse(BaseModel):
    """Response body returned by POST /api/subscribe."""

    status: str
    message: str


def _format_time(iso_timestamp: Optional[str]) -> str:
    """Turn an ISO-8601 timestamp into a short display string, or '' if missing."""
    if not iso_timestamp:
        return ""
    return iso_timestamp[:16].replace("T", " ")


def _describe_wildfire_intensity(frp: Optional[float]) -> str:
    """Translate fire radiative power (a technical satellite reading) into a plain-language label."""
    if frp is None:
        return "unknown"
    if frp < 10:
        return "low"
    if frp < 50:
        return "moderate"
    if frp < 200:
        return "high"
    return "extreme"


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

        depth_km = quake.get("depth_km")
        depth_text = f", about {round(depth_km)} km underground" if depth_km is not None else ""

        events.append(
            DisasterEvent(
                id=f"eq-{quake.get('event_id')}",
                type="earthquake",
                location=quake.get("location") or "Unknown location",
                magnitude=round(magnitude, 1),
                lat=lat,
                lng=lng,
                risk=classify_earthquake_magnitude(magnitude),
                time=_format_time(quake.get("time")),
                description=f"A magnitude {magnitude:.1f} earthquake was detected{depth_text}.",
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
        intensity = _describe_wildfire_intensity(hotspot.get("frp"))
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
                description=f"An active wildfire was detected, burning with {intensity} intensity.",
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
                description=(item.get("description") or item.get("event_name") or "Weather event detected.").capitalize(),
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


def run_analysis_and_shape(
    query: str,
    location: str = "",
    autonomous: bool = False,
    simulated_data: dict | None = None,
) -> AnalyzeResponse:
    """Run the full pipeline and shape the result into an AnalyzeResponse.

    Shared by the POST /api/analyze endpoint, the autonomous background
    monitor (services/scheduler.py), and the demo simulator (/api/simulate),
    so all three produce identically-shaped data. `autonomous` defaults to
    False here so chat/manual requests never trigger the Notifier Agent's
    real email — only the scheduler (and an opted-in simulation) pass True.
    """
    result = run_pipeline(query=query, location=location, autonomous=autonomous, simulated_data=simulated_data)

    return AnalyzeResponse(
        overall_risk=result.get("overall_risk") or "",
        earthquake_risk=result.get("earthquake_risk") or "",
        flood_risk=result.get("flood_risk") or "",
        wildfire_risk=result.get("wildfire_risk") or "",
        alert_triggered=result.get("alert_triggered") or False,
        alert_message=result.get("alert_message") or "",
        final_explanation=result.get("final_explanation") or "",
        final_response=result.get("final_response") or "",
        risk_trend=result.get("risk_trend"),
        notification_sent=result.get("notification_sent") or False,
        simulated=result.get("simulated_data") is not None,
        events=build_dashboard_events(result),
    )


@router.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    """Run the full multi-agent pipeline for the given query/location and return the risk assessment."""
    try:
        return run_analysis_and_shape(request.query, request.location)
    except Exception as e:
        # Raise a proper HTTP error instead of letting the pipeline crash the request
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {e}")


@router.post("/api/trigger-check", response_model=AnalyzeResponse)
def trigger_check():
    """Manually run one autonomous-style global check right now, instead of waiting
    for the next scheduled cycle. Unlike /api/analyze, this DOES run with
    autonomous=True, so it can send a real email to subscribers if risk is
    High/Critical — useful for testing the Notifier Agent without waiting."""
    try:
        return run_analysis_and_shape("Global disaster risk overview", "", autonomous=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {e}")


@router.post("/api/simulate", response_model=AnalyzeResponse)
async def simulate(request: SimulateRequest):
    """Run the real 7-agent pipeline on a synthetic High/Critical scenario,
    for demoing the alert/notification flow without waiting for a real
    disaster. `send_email` opts into a real test email via the Notifier
    Agent; it defaults to off so repeated demo clicks don't spam subscribers.
    Broadcasts live to connected dashboards but is NOT written into the
    permanent risk history, so it can't distort the real trend chart."""
    scenario_builder = SCENARIOS.get(request.scenario)
    if scenario_builder is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{request.scenario}'. Choose one of: {', '.join(SCENARIOS)}",
        )

    location, simulated_data = scenario_builder()

    try:
        response = await asyncio.to_thread(
            run_analysis_and_shape,
            f"Simulated {request.scenario} scenario for demo purposes",
            location,
            request.send_email,
            simulated_data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {e}")

    await broadcast(response.model_dump())
    return response


@router.get("/api/health", response_model=HealthResponse)
def health():
    """Simple health check endpoint to confirm the API is running."""
    return HealthResponse(status="ok", message="StormSense AI is running")


@router.get("/api/history", response_model=List[HistoryEntryResponse])
def history():
    """Return the autonomous monitor's rolling risk history, for the trend chart."""
    return get_history()


@router.post("/api/subscribe", response_model=SubscribeResponse)
def subscribe(request: SubscribeRequest):
    """Register an email to receive real disaster alerts. No login required."""
    try:
        add_subscriber(request.value)
        count = get_subscriber_count()
        return SubscribeResponse(
            status="ok",
            message=f"You're subscribed. ({count} subscriber{'s' if count != 1 else ''} total.)",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
