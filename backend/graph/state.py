# Graph state: defines the shared state schema passed between agents in the LangGraph workflow

from typing import Any, Optional
from typing_extensions import TypedDict


class StormSenseState(TypedDict):
    """Shared state passed between the manager, data, analysis, alert, and writer agents."""

    # The user input or trigger message that kicked off the workflow
    query: str

    # Optional location string (e.g. city, region, or coordinates) to scope data fetching
    location: Optional[str]

    # Raw earthquake data pulled from the USGS API
    raw_earthquake_data: Optional[dict[str, Any]]

    # Raw weather data pulled from the OpenWeatherMap API
    raw_weather_data: Optional[dict[str, Any]]

    # Raw wildfire hotspot data pulled from the NASA FIRMS API
    raw_wildfire_data: Optional[dict[str, Any]]

    # Risk level assessed for earthquakes (e.g. "Low", "Moderate", "High", "Critical")
    earthquake_risk: Optional[str]

    # Risk level assessed for floods (e.g. "Low", "Moderate", "High", "Critical")
    flood_risk: Optional[str]

    # Risk level assessed for wildfires (e.g. "Low", "Moderate", "High", "Critical")
    wildfire_risk: Optional[str]

    # Combined overall risk level across all hazard types
    overall_risk: Optional[str]

    # Explanation of how the risk scores were derived
    risk_reasoning: Optional[str]

    # True if the overall risk is High or Critical, triggering an alert
    alert_triggered: bool

    # The alert text generated when alert_triggered is True
    alert_message: Optional[str]

    # Plain language explanation of the situation, written by the Writer Agent
    final_explanation: Optional[str]

    # The complete combined response sent back to the user
    final_response: Optional[str]
