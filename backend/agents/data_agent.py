# Data agent: fetches raw disaster data from external sources (USGS, weather, FIRMS)

import csv
import io
import os

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


def data_agent(state: StormSenseState) -> StormSenseState:
    """Fetch live earthquake, weather, and wildfire data and store it in the shared state."""
    print("[Data Agent] Starting data collection...")

    location = state.get("location") or DEFAULT_WEATHER_LOCATION

    state["raw_earthquake_data"] = fetch_earthquake_data()
    state["raw_weather_data"] = fetch_weather_data(location)
    state["raw_wildfire_data"] = fetch_wildfire_data()

    print("[Data Agent] Data collection complete.")
    return state
