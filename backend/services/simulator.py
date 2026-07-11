# Demo scenario builder: produces realistic, correctly-shaped synthetic raw
# data (matching USGS/OpenWeatherMap/NASA FIRMS response formats exactly) so
# the *real* pipeline — Data, Analysis, Alert, Forecast, Writer, Notifier —
# runs end to end on it, instead of faking a risk score directly. This exists
# so a High/Critical alert can be demoed live without waiting for an actual
# disaster to occur somewhere in the world during judging.

from datetime import datetime, timezone
from typing import Callable


def _now_epoch_millis() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _earthquake_scenario() -> tuple[str, dict]:
    """A magnitude 7.8 quake near Tokyo — well past the 7.0 Critical threshold."""
    location = "Tokyo, Japan"
    raw_earthquake_data = {
        "features": [
            {
                "properties": {
                    "mag": 7.8,
                    "place": "62km ESE of Tokyo, Japan",
                    "time": _now_epoch_millis(),
                    "magType": "mww",
                    "tsunami": 1,
                    "alert": "red",
                    "sig": 2000,
                    "status": "reviewed",
                },
                "geometry": {"type": "Point", "coordinates": [140.1, 35.5, 24.0]},
                "id": "demo-eq-simulated",
            }
        ]
    }
    raw_weather_data = {
        "name": location,
        "coord": {"lon": 139.69, "lat": 35.69},
        "weather": [{"id": 800, "main": "Clear", "description": "clear sky"}],
        "dt": int(datetime.now(timezone.utc).timestamp()),
    }
    raw_wildfire_data = {"hotspots": []}
    return location, {
        "raw_earthquake_data": raw_earthquake_data,
        "raw_weather_data": raw_weather_data,
        "raw_wildfire_data": raw_wildfire_data,
    }


def _wildfire_scenario() -> tuple[str, dict]:
    """35 high-intensity FIRMS hotspots clustered near Los Angeles — past the 30-hotspot Critical threshold."""
    location = "Los Angeles, USA"
    now = datetime.now(timezone.utc)
    acq_date = now.strftime("%Y-%m-%d")
    acq_time = now.strftime("%H%M")

    hotspots = []
    base_lat, base_lon = 34.05, -118.25
    for i in range(35):
        hotspots.append(
            {
                "latitude": str(base_lat + (i % 7) * 0.03),
                "longitude": str(base_lon + (i // 7) * 0.03),
                "brightness": "345.2",
                "acq_date": acq_date,
                "acq_time": acq_time,
                "satellite": "N",
                "instrument": "VIIRS",
                "confidence": "high",
                "frp": "180.5",
                "daynight": "D",
            }
        )

    raw_earthquake_data = {"features": []}
    raw_weather_data = {
        "name": location,
        "coord": {"lon": -118.24, "lat": 34.05},
        "weather": [{"id": 800, "main": "Clear", "description": "clear sky"}],
        "dt": int(now.timestamp()),
    }
    raw_wildfire_data = {"hotspots": hotspots}
    return location, {
        "raw_earthquake_data": raw_earthquake_data,
        "raw_weather_data": raw_weather_data,
        "raw_wildfire_data": raw_wildfire_data,
    }


def _flood_scenario() -> tuple[str, dict]:
    """Extreme rain (weather id 522, plus 65mm/hr) near Manila — past the High-risk thunderstorm/heavy-rain threshold."""
    location = "Manila, Philippines"
    now = datetime.now(timezone.utc)
    raw_earthquake_data = {"features": []}
    raw_weather_data = {
        "name": location,
        "coord": {"lon": 120.98, "lat": 14.6},
        "weather": [{"id": 522, "main": "Rain", "description": "extreme rain"}],
        "rain": {"1h": 65.0},
        "wind": {"speed": 12.5},
        "dt": int(now.timestamp()),
    }
    raw_wildfire_data = {"hotspots": []}
    return location, {
        "raw_earthquake_data": raw_earthquake_data,
        "raw_weather_data": raw_weather_data,
        "raw_wildfire_data": raw_wildfire_data,
    }


SCENARIOS: dict[str, Callable[[], tuple[str, dict]]] = {
    "earthquake": _earthquake_scenario,
    "wildfire": _wildfire_scenario,
    "flood": _flood_scenario,
}
