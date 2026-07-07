"""
backend/tools/weather_tool.py

Parsing helper for the StormSense AI Data Agent.

This module does NOT perform any network calls. It only takes an
already-fetched raw response from the OpenWeatherMap API and converts it
into the clean, standardized structure StormSense AI's Analysis Agent
expects, covering current conditions plus any active storm/flood
warnings.

This parser is written to tolerate the two shapes OpenWeatherMap
commonly returns, since either may be used by the Data Agent:

1. Current weather / conditions payload, e.g.:
{
  "name": "Lahore",
  "coord": {"lon": 74.34, "lat": 31.55},
  "weather": [{"id": 200, "main": "Thunderstorm", "description":
      "thunderstorm with heavy rain"}],
  "main": {"temp": 29.4, "humidity": 88},
  "rain": {"1h": 12.5},
  "wind": {"speed": 14.2},
  "dt": 1751880000
}

2. An "alerts" payload (e.g. from the One Call API), e.g.:
{
  "alerts": [
    {
      "sender_name": "National Weather Service",
      "event": "Flood Warning",
      "start": 1751880000,
      "end": 1751901600,
      "description": "Heavy rainfall expected to cause flash flooding...",
      "tags": ["Flood"]
    },
    ...
  ]
}

A response may contain either or both shapes. Every field is read
defensively with .get() since OpenWeatherMap does not guarantee any
particular field will be present for a given location or plan tier.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# Weather condition codes (OpenWeatherMap "id" field, first digit) that
# indicate storm/flood-relevant severe weather, used to derive a rough
# severity label when no explicit "alerts" entry is present.
_SEVERE_CONDITION_GROUPS = {
    2: "storm",     # Thunderstorm
    5: "rain",      # Rain (heavy rain can indicate flood risk)
    6: "snow",      # Snow
    7: "atmosphere",  # Fog, dust, tornado, etc.
}


def _epoch_seconds_to_iso(epoch_seconds: Optional[float]) -> Optional[str]:
    """Convert an OpenWeatherMap epoch-seconds timestamp to ISO-8601 UTC.

    Args:
        epoch_seconds: Seconds since the Unix epoch, as used throughout
            OpenWeatherMap's API (fields like "dt", "start", "end").
            May be None.

    Returns:
        An ISO-8601 formatted UTC timestamp string, or None if the input
        was missing or could not be parsed.
    """
    if epoch_seconds is None:
        return None
    try:
        return datetime.fromtimestamp(
            float(epoch_seconds), tz=timezone.utc
        ).isoformat()
    except (TypeError, ValueError):
        return None


def _parse_alert_entries(
    raw_response: Dict[str, Any], area: Optional[str]
) -> List[Dict[str, Any]]:
    """Parse the "alerts" list of an OpenWeatherMap response, if present.

    Args:
        raw_response: The raw OpenWeatherMap API response.
        area: A human-readable location label to attach to each parsed
            alert (e.g. the city name or "lat,lon" string), if known.

    Returns:
        A list of standardized weather event dicts derived from official
        alert entries. Empty if no "alerts" key is present.
    """
    alerts = raw_response.get("alerts") or []
    if not isinstance(alerts, list):
        return []

    parsed_alerts: List[Dict[str, Any]] = []
    for alert in alerts:
        if not isinstance(alert, dict):
            continue

        event_name = alert.get("event") or "Weather Alert"
        tags = alert.get("tags") or []
        event_type = _classify_event_type(event_name, tags)

        parsed_alerts.append(
            {
                "type": event_type,
                "event_name": event_name,
                "area": area,
                "severity": "High" if event_type in ("flood", "storm") else "Medium",
                "description": alert.get("description"),
                "sender": alert.get("sender_name"),
                "issued_at": _epoch_seconds_to_iso(alert.get("start")),
                "expires_at": _epoch_seconds_to_iso(alert.get("end")),
                "source": "openweathermap_alert",
            }
        )

    return parsed_alerts


def _classify_event_type(event_name: str, tags: List[str]) -> str:
    """Classify a raw alert event name/tags into StormSense's event types.

    Args:
        event_name: The raw "event" string from OpenWeatherMap
            (e.g. "Flood Warning", "Severe Thunderstorm Warning").
        tags: The raw "tags" list from OpenWeatherMap, if any.

    Returns:
        One of "flood", "storm", or "weather" (generic fallback).
    """
    lowered_name = (event_name or "").lower()
    lowered_tags = [str(tag).lower() for tag in tags]

    if "flood" in lowered_name or "flood" in lowered_tags:
        return "flood"
    if any(
        keyword in lowered_name
        for keyword in ("storm", "hurricane", "cyclone", "tornado", "wind")
    ):
        return "storm"
    return "weather"


def _parse_current_conditions(
    raw_response: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Parse the current-conditions portion of an OpenWeatherMap response.

    This captures cases where no official "alerts" entry exists yet, but
    the current conditions (e.g. heavy rain, thunderstorm) still carry
    flood/storm relevance for the Analysis Agent.

    Args:
        raw_response: The raw OpenWeatherMap API response.

    Returns:
        A single standardized weather event dict summarizing current
        conditions, or None if no relevant "weather" data is present.
    """
    weather_conditions = raw_response.get("weather") or []
    if not isinstance(weather_conditions, list) or not weather_conditions:
        return None

    primary_condition = weather_conditions[0] if isinstance(
        weather_conditions[0], dict
    ) else {}

    condition_id = primary_condition.get("id")
    condition_group = (condition_id // 100) if isinstance(condition_id, int) else None
    condition_category = _SEVERE_CONDITION_GROUPS.get(condition_group, "weather")

    area = raw_response.get("name")
    coord = raw_response.get("coord") or {}
    rain = raw_response.get("rain") or {}
    wind = raw_response.get("wind") or {}

    rain_last_hour_mm = rain.get("1h")
    is_heavy_rain = isinstance(rain_last_hour_mm, (int, float)) and rain_last_hour_mm >= 10

    event_type = "flood" if is_heavy_rain else (
        "storm" if condition_category == "storm" else "weather"
    )

    return {
        "type": event_type,
        "event_name": primary_condition.get("main"),
        "area": area,
        "coordinates": {
            "latitude": coord.get("lat"),
            "longitude": coord.get("lon"),
        },
        "severity": "High" if (is_heavy_rain or condition_category == "storm") else "Low",
        "description": primary_condition.get("description"),
        "rain_last_hour_mm": rain_last_hour_mm,
        "wind_speed_mps": wind.get("speed"),
        "issued_at": _epoch_seconds_to_iso(raw_response.get("dt")),
        "expires_at": None,
        "source": "openweathermap_current",
    }


def parse_weather_data(raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Clean and structure a raw OpenWeatherMap API response.

    Takes the raw payload returned by OpenWeatherMap (already fetched
    elsewhere in the pipeline) and converts it into a list of
    standardized weather/flood/storm event dictionaries that the
    Analysis Agent can consume directly. Handles both official "alerts"
    entries and current-conditions data, since either may be relevant
    to flood or storm risk.

    Args:
        raw_response: The raw, already-fetched OpenWeatherMap API
            response as a Python dict. May contain a "weather" list
            (current conditions), an "alerts" list (official warnings),
            both, or neither. A missing or malformed response degrades
            to an empty list rather than raising an exception.

    Returns:
        A list of dicts, each shaped as:
            {
                "type": "flood" | "storm" | "weather",
                "event_name": str | None,
                "area": str | None,
                "severity": "Low" | "Medium" | "High",
                "description": str | None,
                "issued_at": str | None,   # ISO-8601 UTC
                "expires_at": str | None,  # ISO-8601 UTC
                "source": str,
                ... additional context fields depending on origin ...
            }
        Returns an empty list if raw_response is empty, malformed, or
        contains no usable weather/alert data.
    """
    if not isinstance(raw_response, dict):
        return []

    area = raw_response.get("name")
    events: List[Dict[str, Any]] = []

    events.extend(_parse_alert_entries(raw_response, area))

    current_conditions_event = _parse_current_conditions(raw_response)
    if current_conditions_event is not None:
        events.append(current_conditions_event)

    return events