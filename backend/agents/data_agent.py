# Data agent: fetches raw disaster data from external sources (USGS, weather, FIRMS)

import csv
import io
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

import requests
from dotenv import load_dotenv

from graph.state import StormSenseState

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NASA_FIRMS_API_KEY = os.getenv("NASA_FIRMS_API_KEY")

USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FIRMS_URL_TEMPLATE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{api_key}/VIIRS_SNPP_NRT/-180,-90,180,90/1"

DEFAULT_WEATHER_LOCATION = "New York"


def fetch_earthquake_data() -> dict:
    """Fetch live earthquake data (magnitude 4.0+) from the USGS API."""
    print("[Data Agent] Fetching earthquake data from USGS...")
    try:
        params = {
            "format": "geojson",
            "limit": 10,
            "minmagnitude": 4.0,
            "orderby": "time",
        }
        response = requests.get(USGS_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"[Data Agent] USGS returned {len(data.get('features', []))} earthquake events.")
        return data
    except Exception as e:
        print(f"[Data Agent] Failed to fetch USGS earthquake data: {e}")
        return {}


def fetch_weather_data(location: str = DEFAULT_WEATHER_LOCATION) -> dict:
    """Fetch live current weather data for a location from OpenWeatherMap."""
    print(f"[Data Agent] Fetching weather data from OpenWeatherMap for '{location}'...")
    try:
        if not OPENWEATHER_API_KEY:
            raise ValueError("OPENWEATHER_API_KEY is not set in the environment.")

        params = {
            "q": location,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
        }
        response = requests.get(OPENWEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"[Data Agent] OpenWeatherMap returned weather data for '{location}'.")
        return data
    except Exception as e:
        print(f"[Data Agent] Failed to fetch OpenWeatherMap weather data: {e}")
        return {}


def fetch_wildfire_data() -> dict:
    """Fetch live global wildfire hotspot data from NASA FIRMS."""
    print("[Data Agent] Fetching wildfire hotspot data from NASA FIRMS...")
    try:
        if not NASA_FIRMS_API_KEY:
            raise ValueError("NASA_FIRMS_API_KEY is not set in the environment.")

        url = FIRMS_URL_TEMPLATE.format(api_key=NASA_FIRMS_API_KEY)
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        reader = csv.DictReader(io.StringIO(response.text))
        hotspots = list(reader)
        print(f"[Data Agent] NASA FIRMS returned {len(hotspots)} active fire hotspots.")
        return {"hotspots": hotspots}
    except Exception as e:
        print(f"[Data Agent] Failed to fetch NASA FIRMS wildfire data: {e}")
        return {}


def _get_with_deadline(future, source_name: str, deadline_seconds: float) -> dict:
    """Wait for a fetch future up to a hard wall-clock deadline, falling back to {} past it.

    requests' own `timeout=` only bounds each individual read chunk, not the
    total request duration — a large response that trickles in slowly (like
    NASA FIRMS' global CSV) can still take far longer overall. This enforces
    an actual ceiling on how long any one source can hold up the pipeline.
    """
    try:
        return future.result(timeout=deadline_seconds)
    except FutureTimeoutError:
        print(f"[Data Agent] {source_name} exceeded the {deadline_seconds}s deadline, continuing without it.")
        return {}


def data_agent(state: StormSenseState) -> StormSenseState:
    """Fetch live earthquake, weather, and wildfire data and store it in the shared state."""
    simulated = state.get("simulated_data")
    if simulated:
        print("[Data Agent] Using simulated scenario data — skipping live API calls.")
        state["raw_earthquake_data"] = simulated.get("raw_earthquake_data") or {}
        state["raw_weather_data"] = simulated.get("raw_weather_data") or {}
        state["raw_wildfire_data"] = simulated.get("raw_wildfire_data") or {}
        return state

    print("[Data Agent] Starting data collection...")

    location = state.get("location") or DEFAULT_WEATHER_LOCATION

    # These three API calls are independent, so run them concurrently instead
    # of sequentially — the slowest one (usually NASA FIRMS) sets the total
    # time instead of all three stacking up, which is what was pushing total
    # pipeline latency past the frontend proxy's timeout. Each also gets a
    # hard wall-clock deadline so one slow source can't block the others.
    #
    # Note: this deliberately does NOT use `with ThreadPoolExecutor() as executor:`
    # — that context manager calls shutdown(wait=True) on exit, which blocks
    # until every submitted thread finishes even if we already gave up on it
    # via .result(timeout=...), silently defeating the whole point of the
    # deadline. shutdown(wait=False) lets us move on and abandon slow threads;
    # they finish harmlessly in the background and get garbage collected.
    executor = ThreadPoolExecutor(max_workers=3)
    earthquake_future = executor.submit(fetch_earthquake_data)
    weather_future = executor.submit(fetch_weather_data, location)
    wildfire_future = executor.submit(fetch_wildfire_data)

    state["raw_earthquake_data"] = _get_with_deadline(earthquake_future, "USGS", 12)
    state["raw_weather_data"] = _get_with_deadline(weather_future, "OpenWeatherMap", 12)
    state["raw_wildfire_data"] = _get_with_deadline(wildfire_future, "NASA FIRMS", 18)
    executor.shutdown(wait=False)

    print("[Data Agent] Data collection complete.")
    return state
