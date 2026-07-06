# Analysis agent: interprets and analyzes disaster data to assess risk and severity

from graph.state import StormSenseState

RISK_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}


def analyze_earthquake_risk(raw_earthquake_data: dict) -> tuple[str, float]:
    """Determine earthquake risk from the highest magnitude in the USGS feature list."""
    features = (raw_earthquake_data or {}).get("features", [])

    # No events at all means no earthquake risk
    if not features:
        return "Low", 0.0

    # Find the highest magnitude among all returned events
    magnitudes = [
        f["properties"]["mag"]
        for f in features
        if f.get("properties", {}).get("mag") is not None
    ]
    if not magnitudes:
        return "Low", 0.0

    max_magnitude = max(magnitudes)

    if max_magnitude >= 7.0:
        risk = "Critical"
    elif max_magnitude >= 6.0:
        risk = "High"
    elif max_magnitude >= 5.0:
        risk = "Medium"
    else:
        risk = "Low"

    return risk, max_magnitude


def analyze_flood_risk(raw_weather_data: dict) -> tuple[str, int | None]:
    """Determine flood risk from the OpenWeatherMap weather condition id."""
    weather_list = (raw_weather_data or {}).get("weather", [])

    # No weather data means no basis for flood risk
    if not weather_list:
        return "Low", None

    weather_id = weather_list[0].get("id")
    if weather_id is None:
        return "Low", None

    # Thunderstorm codes (200-232) are treated as high risk
    if 200 <= weather_id <= 232:
        risk = "High"
    # Extreme/heavy rain and rain showers (511-531) are treated as high risk
    elif 511 <= weather_id <= 531:
        risk = "High"
    # Light to heavy rain (500-504) is treated as medium risk
    elif 500 <= weather_id <= 504:
        risk = "Medium"
    else:
        risk = "Low"

    return risk, weather_id


def analyze_wildfire_risk(raw_wildfire_data: dict) -> tuple[str, int]:
    """Determine wildfire risk from the number of active FIRMS hotspots."""
    hotspots = (raw_wildfire_data or {}).get("hotspots", [])
    hotspot_count = len(hotspots)

    if hotspot_count > 30:
        risk = "Critical"
    elif hotspot_count >= 16:
        risk = "High"
    elif hotspot_count >= 5:
        risk = "Medium"
    else:
        risk = "Low"

    return risk, hotspot_count


def analysis_agent(state: StormSenseState) -> StormSenseState:
    """Read raw data from the state and compute per-hazard and overall risk levels."""
    print("[Analysis Agent] Analyzing risk levels from raw data...")

    earthquake_risk, max_magnitude = analyze_earthquake_risk(state.get("raw_earthquake_data"))
    flood_risk, weather_id = analyze_flood_risk(state.get("raw_weather_data"))
    wildfire_risk, hotspot_count = analyze_wildfire_risk(state.get("raw_wildfire_data"))

    state["earthquake_risk"] = earthquake_risk
    state["flood_risk"] = flood_risk
    state["wildfire_risk"] = wildfire_risk

    # Overall risk is the highest severity among the three individual hazard risks
    all_risks = [earthquake_risk, flood_risk, wildfire_risk]
    overall_risk = max(all_risks, key=lambda r: RISK_ORDER[r])
    state["overall_risk"] = overall_risk

    # Build a brief human-readable summary of how each risk was determined
    reasoning_parts = [
        f"Earthquake risk is {earthquake_risk} (highest magnitude observed: {max_magnitude}).",
        f"Flood risk is {flood_risk} (weather condition id: {weather_id}).",
        f"Wildfire risk is {wildfire_risk} ({hotspot_count} active hotspots detected).",
        f"Overall risk is assessed as {overall_risk}.",
    ]
    state["risk_reasoning"] = " ".join(reasoning_parts)

    print(f"[Analysis Agent] {state['risk_reasoning']}")
    return state
