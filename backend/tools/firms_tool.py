"""
backend/tools/firms_tool.py

Parsing helper for the StormSense AI Data Agent.

This module does NOT perform any network calls. It only takes an
already-fetched raw response from the NASA FIRMS (Fire Information for
Resource Management System) API and converts it into the clean,
standardized structure StormSense AI's Analysis Agent expects.

NASA FIRMS active-fire data is natively CSV, but by the time it reaches
this parser it is expected to already have been converted into a list
of row dicts (e.g. via csv.DictReader or an equivalent JSON wrapper
around the FIRMS response), one dict per detected fire hotspot, such as:

{
  "latitude": "31.5497",
  "longitude": "74.3436",
  "brightness": "312.4",
  "scan": "1.1",
  "track": "1.0",
  "acq_date": "2026-07-07",
  "acq_time": "0512",
  "satellite": "N",
  "instrument": "VIIRS",
  "confidence": "nominal",
  "version": "2.0NRT",
  "bright_t31": "289.6",
  "frp": "45.8",
  "daynight": "D"
}

FIRMS returns all values as strings (since the source is CSV), and does
not provide a "spread direction" field directly — spread direction is
not something the raw hotspot detections encode on their own. This
parser exposes what FIRMS actually provides and marks derived/unknown
fields honestly rather than fabricating them, since the Analysis Agent
must not receive invented data.

Every field is read defensively with .get() since not every FIRMS
product/version includes every column.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _to_float(value: Any) -> Optional[float]:
    """Safely convert a raw FIRMS field to a float.

    FIRMS delivers all values as strings, so numeric fields need
    explicit, defensive conversion.

    Args:
        value: The raw value to convert, of unknown/untrusted type.

    Returns:
        The parsed float, or None if conversion is not possible.
    """
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _combine_acquisition_datetime(
    acq_date: Optional[str], acq_time: Optional[str]
) -> Optional[str]:
    """Combine FIRMS's separate acq_date and acq_time fields into ISO-8601.

    FIRMS reports date as "YYYY-MM-DD" and time as a zero-padded 24-hour
    "HHMM" string (UTC), e.g. acq_date="2026-07-07", acq_time="0512".

    Args:
        acq_date: The raw acquisition date string, or None.
        acq_time: The raw acquisition time string ("HHMM"), or None.

    Returns:
        An ISO-8601 UTC timestamp string, or None if either input is
        missing or cannot be parsed.
    """
    if not acq_date or acq_time is None:
        return None

    time_str = str(acq_time).zfill(4)
    if len(time_str) != 4 or not time_str.isdigit():
        return None

    try:
        combined = datetime.strptime(
            f"{acq_date} {time_str[:2]}:{time_str[2:]}",
            "%Y-%m-%d %H:%M",
        ).replace(tzinfo=timezone.utc)
        return combined.isoformat()
    except ValueError:
        return None


def _confidence_to_label(raw_confidence: Any) -> Optional[str]:
    """Normalize FIRMS's confidence field, which varies by instrument.

    VIIRS products use text labels ("low", "nominal", "high"); MODIS
    products use a numeric 0-100 percentage. This normalizes both into
    a consistent text label where possible, and passes through the raw
    value if it doesn't match a known pattern.

    Args:
        raw_confidence: The raw "confidence" field value from FIRMS.

    Returns:
        A normalized confidence label, or None if not provided.
    """
    if raw_confidence is None or raw_confidence == "":
        return None

    text_value = str(raw_confidence).strip().lower()
    if text_value in ("low", "nominal", "high"):
        return text_value

    numeric_value = _to_float(raw_confidence)
    if numeric_value is not None:
        if numeric_value < 30:
            return "low"
        if numeric_value < 80:
            return "nominal"
        return "high"

    return text_value


def _parse_single_hotspot(record: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single FIRMS hotspot record into StormSense's wildfire schema.

    Args:
        record: One row of already-fetched FIRMS data, as a dict.

    Returns:
        A standardized wildfire event dict.
    """
    latitude = _to_float(record.get("latitude"))
    longitude = _to_float(record.get("longitude"))

    return {
        "location": (
            f"{latitude}, {longitude}"
            if latitude is not None and longitude is not None
            else None
        ),
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "frp": _to_float(record.get("frp")),  # Fire Radiative Power (MW)
        "brightness": _to_float(record.get("brightness")),
        "bright_t31": _to_float(record.get("bright_t31")),
        "confidence": _confidence_to_label(record.get("confidence")),
        "satellite": record.get("satellite"),
        "instrument": record.get("instrument"),
        "daynight": record.get("daynight"),
        # NASA FIRMS hotspot detections do not directly report a fire
        # spread direction; that would require comparing sequential
        # detections over time, which is outside this parser's scope.
        # Exposed honestly as unknown rather than fabricated.
        "spread_direction": None,
        "detected_at": _combine_acquisition_datetime(
            record.get("acq_date"), record.get("acq_time")
        ),
        "product_version": record.get("version"),
    }


def parse_wildfire_data(raw_response: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean and structure a raw NASA FIRMS API response.

    Takes the raw, already-fetched FIRMS active-fire hotspot records
    (a list of row dicts, typically produced by parsing the FIRMS CSV
    output) and converts them into a list of standardized wildfire event
    dictionaries that the Analysis Agent can consume directly.

    Args:
        raw_response: The raw, already-fetched FIRMS data as a list of
            dicts, one per detected hotspot. A missing, empty, or
            malformed input degrades to an empty list rather than
            raising an exception.

    Returns:
        A list of dicts, each shaped as:
            {
                "location": str | None,        # "lat, lon" convenience label
                "coordinates": {
                    "latitude": float | None,
                    "longitude": float | None,
                },
                "frp": float | None,            # Fire Radiative Power (MW)
                "brightness": float | None,
                "bright_t31": float | None,
                "confidence": str | None,       # "low" | "nominal" | "high"
                "satellite": str | None,
                "instrument": str | None,
                "daynight": str | None,         # "D" | "N"
                "spread_direction": None,       # not derivable from raw data
                "detected_at": str | None,      # ISO-8601 UTC
                "product_version": str | None,
            }
        Returns an empty list if raw_response is empty or malformed.
    """
    if not isinstance(raw_response, list):
        return []

    parsed_hotspots: List[Dict[str, Any]] = []
    for record in raw_response:
        if not isinstance(record, dict):
            continue
        parsed_hotspots.append(_parse_single_hotspot(record))

    return parsed_hotspots