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

    # True only for scheduled background runs (the autonomous monitor), never
    # for user-initiated chat queries — gates real-world side effects like
    # sending an email so asking a question never spams a notification
    autonomous: Optional[bool]

    # True if the Notifier Agent actually sent a real email this run
    notification_sent: Optional[bool]

    # Plain-language description of how risk has changed recently (e.g.
    # "Wildfire risk has risen from Medium to Critical in the last hour"),
    # produced by the Forecast Agent from recent history. None if there
    # isn't enough history yet to compare against.
    risk_trend: Optional[str]

    # When set, the Data Agent uses this pre-built raw data instead of
    # calling the live APIs — powers the "Simulate Critical Event" demo
    # feature so a High/Critical alert can be shown without waiting for a
    # real disaster. Every agent after Data runs for real on this data.
    simulated_data: Optional[dict[str, Any]]
