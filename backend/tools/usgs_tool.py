"""
backend/tools/usgs_tool.py

Parsing helper for the StormSense AI Data Agent.

This module does NOT perform any network calls. It only takes an
already-fetched raw response from the USGS Earthquake API (GeoJSON
format, e.g. from an endpoint such as
https://earthquake.usgs.gov/earthquakemap/feed/v1.0/summary/*.geojson)
and converts it into the clean, standardized structure StormSense AI's
Analysis Agent expects.

USGS GeoJSON responses look roughly like:

{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "mag": 6.5,
        "place": "80km from Lahore, Pakistan",
        "time": 1751880000000,          # epoch millis
        "updated": 1751880500000,
        "tsunami": 0,
        "alert": "yellow",
        "sig": 650,
        "magType": "mb",
        "type": "earthquake",
        "status": "reviewed"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [74.3436, 31.5497, 10.0]  # [lon, lat, depth_km]
      },
      "id": "us7000abcd"
    },
    ...
  ]
}

Any of these fields may be missing or null in practice, so every field
is read defensively with .get() and never assumed to be present.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _epoch_millis_to_iso(epoch_millis: Optional[float]) -> Optional[str]:
    """Convert a USGS epoch-milliseconds timestamp to an ISO-8601 UTC string.

    Args:
        epoch_millis: Milliseconds since the Unix epoch, as provided by
            USGS in the "time" property. May be None.

    Returns:
        An ISO-8601 formatted UTC timestamp string, or None if the input
        was missing or could not be parsed.
    """
    if epoch_millis is None:
        return None
    try:
        seconds = float(epoch_millis) / 1000.0
        return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


def _extract_coordinates(
    geometry: Optional[Dict[str, Any]]
) -> Dict[str, Optional[float]]:
    """Safely pull longitude, latitude, and depth out of a GeoJSON geometry.

    USGS orders coordinates as [longitude, latitude, depth_km].

    Args:
        geometry: The "geometry" object from a USGS feature, or None.

    Returns:
        A dict with "latitude", "longitude", and "depth_km" keys. Any
        value that cannot be determined is set to None.
    """
    coords = (geometry or {}).get("coordinates") or []
    longitude = coords[0] if len(coords) > 0 else None
    latitude = coords[1] if len(coords) > 1 else None
    depth_km = coords[2] if len(coords) > 2 else None
    return {
        "latitude": latitude,
        "longitude": longitude,
        "depth_km": depth_km,
    }


def _parse_single_feature(feature: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single USGS GeoJSON feature into StormSense's earthquake schema.

    Args:
        feature: One item from the USGS response's "features" list.

    Returns:
        A standardized earthquake event dict.
    """
    properties = feature.get("properties") or {}
    geometry = feature.get("geometry") or {}
    location_data = _extract_coordinates(geometry)

    return {
        "event_id": feature.get("id"),
        "magnitude": properties.get("mag"),
        "magnitude_type": properties.get("magType"),
        "location": properties.get("place"),
        "coordinates": {
            "latitude": location_data["latitude"],
            "longitude": location_data["longitude"],
        },
        "depth_km": location_data["depth_km"],
        "time": _epoch_millis_to_iso(properties.get("time")),
        "updated": _epoch_millis_to_iso(properties.get("updated")),
        "tsunami_warning": bool(properties.get("tsunami", 0)),
        "usgs_alert_level": properties.get("alert"),
        "significance": properties.get("sig"),
        "status": properties.get("status"),
    }


def parse_earthquake_data(raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Clean and structure a raw USGS Earthquake API response.

    Takes the raw GeoJSON payload returned by the USGS Earthquake API
    (already fetched elsewhere in the pipeline) and converts it into a
    list of standardized earthquake event dictionaries that the Analysis
    Agent can consume directly, without needing to know anything about
    USGS's native GeoJSON structure.

    Args:
        raw_response: The raw, already-fetched USGS API response as a
            Python dict (i.e. json.loads() of the API's JSON body).
            Expected to contain a "features" list, but this is not
            assumed — a missing or malformed response degrades to an
            empty list rather than raising an exception.

    Returns:
        A list of dicts, each shaped as:
            {
                "event_id": str | None,
                "magnitude": float | None,
                "magnitude_type": str | None,
                "location": str | None,
                "coordinates": {
                    "latitude": float | None,
                    "longitude": float | None,
                },
                "depth_km": float | None,
                "time": str | None,          # ISO-8601 UTC
                "updated": str | None,        # ISO-8601 UTC
                "tsunami_warning": bool,
                "usgs_alert_level": str | None,
                "significance": int | None,
                "status": str | None,
            }
        Returns an empty list if raw_response is empty, malformed, or
        contains no features.
    """
    if not isinstance(raw_response, dict):
        return []

    features = raw_response.get("features") or []
    if not isinstance(features, list):
        return []

    parsed_events: List[Dict[str, Any]] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        parsed_events.append(_parse_single_feature(feature))

    return parsed_events