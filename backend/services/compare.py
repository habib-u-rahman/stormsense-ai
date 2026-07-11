# Compare feature: assesses risk for several named locations at once, for
# the on-demand "Compare Risk Across Locations" panel. Deliberately isolated
# from the main graph/pipeline (graph/workflow.py, agents/data_agent.py) —
# it only reuses their pure, already-existing fetch/analysis functions
# unchanged, and never touches shared state, the live dashboard, history, or
# the WebSocket broadcast. A comparison run affects nothing outside its own
# response.
#
# USGS and NASA FIRMS are global feeds, not scoped to a location — the main
# dashboard shows all of it on purpose. But for a location-by-location
# comparison to actually differ between cities, earthquake/wildfire data
# needs to be filtered to what's near each one. OpenWeatherMap's city lookup
# already returns coordinates for the queried city, so those are reused
# instead of adding a separate geocoding dependency.

import math
from typing import Any, Optional

from agents.alert_agent import alert_agent
from agents.analysis_agent import analysis_agent
from agents.data_agent import fetch_weather_data

# Approximate "regional relevance" radii — not a precise seismic/fire-science
# boundary, just a reasonable cutoff for "this event is near this city."
EARTHQUAKE_RADIUS_KM = 500
WILDFIRE_RADIUS_KM = 300

_EARTH_RADIUS_KM = 6371.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _filter_earthquakes_near(raw_earthquake_data: dict, lat: float, lon: float) -> dict:
    features = (raw_earthquake_data or {}).get("features", [])
    nearby = []
    for feature in features:
        coords = (feature.get("geometry") or {}).get("coordinates") or []
        if len(coords) < 2:
            continue
        quake_lon, quake_lat = coords[0], coords[1]
        if _haversine_km(lat, lon, quake_lat, quake_lon) <= EARTHQUAKE_RADIUS_KM:
            nearby.append(feature)
    return {"features": nearby}


def _filter_wildfires_near(raw_wildfire_data: dict, lat: float, lon: float) -> dict:
    hotspots = (raw_wildfire_data or {}).get("hotspots", [])
    nearby = []
    for hotspot in hotspots:
        try:
            h_lat = float(hotspot.get("latitude"))
            h_lon = float(hotspot.get("longitude"))
        except (TypeError, ValueError):
            continue
        if _haversine_km(lat, lon, h_lat, h_lon) <= WILDFIRE_RADIUS_KM:
            nearby.append(hotspot)
    return {"hotspots": nearby}


def assess_location(location: str, global_earthquake_data: dict, global_wildfire_data: dict) -> dict[str, Any]:
    """Assess risk for one location, using earthquake/wildfire data scoped to
    what's actually near it. Runs the same analysis/alert logic the main
    pipeline uses, just without the Data Agent's network calls (the global
    feeds are passed in already-fetched, once, and shared across every
    location in a comparison request) and without the Writer/Notifier steps,
    since this only needs a risk table, not a written explanation or a
    real-world email side effect.
    """
    weather = fetch_weather_data(location)
    coord = (weather or {}).get("coord") or {}
    lat, lon = coord.get("lat"), coord.get("lon")

    if lat is None or lon is None:
        return {"location": location, "error": f"Couldn't find weather data for '{location}'."}

    state: dict[str, Any] = {
        "raw_earthquake_data": _filter_earthquakes_near(global_earthquake_data, lat, lon),
        "raw_weather_data": weather,
        "raw_wildfire_data": _filter_wildfires_near(global_wildfire_data, lat, lon),
    }
    state = analysis_agent(state)
    state = alert_agent(state)

    return {
        "location": location,
        "overall_risk": state.get("overall_risk") or "Low",
        "earthquake_risk": state.get("earthquake_risk") or "Low",
        "flood_risk": state.get("flood_risk") or "Low",
        "wildfire_risk": state.get("wildfire_risk") or "Low",
        "alert_triggered": state.get("alert_triggered") or False,
    }
