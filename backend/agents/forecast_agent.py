# Forecast Agent: compares the current risk assessment against recent
# history to describe whether things are getting better or worse, adding a
# trend dimension beyond a single point-in-time snapshot. Read-only (never
# sends anything, never writes history) so it's safe to run on every
# pipeline invocation, chat-triggered or autonomous alike.

from typing import Optional

from graph.state import StormSenseState
from services.history import get_history

RISK_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}

# How far back into history to compare against for a trend statement
# (roughly 30 minutes at the default 3-minute autonomous poll interval)
LOOKBACK_ENTRIES = 10


def _describe_change(category_label: str, past_risk: str, current_risk: str) -> Optional[str]:
    """Describe how a single hazard's risk has changed, or None if it hasn't moved."""
    past_rank = RISK_ORDER.get(past_risk, 0)
    current_rank = RISK_ORDER.get(current_risk, 0)

    if current_rank > past_rank:
        return f"{category_label} risk has risen from {past_risk} to {current_risk}"
    if current_rank < past_rank:
        return f"{category_label} risk has eased from {past_risk} to {current_risk}"
    return None


def forecast_agent(state: StormSenseState) -> StormSenseState:
    """Compare current risk against recent history and describe the trend, if any."""
    print("[Forecast Agent] Comparing current risk against recent history...")

    history = get_history()

    if len(history) < 2:
        print("[Forecast Agent] Not enough history yet to describe a trend.")
        state["risk_trend"] = None
        return state

    baseline = history[max(0, len(history) - LOOKBACK_ENTRIES)]

    changes = []
    for label, key in [
        ("Overall", "overall_risk"),
        ("Earthquake", "earthquake_risk"),
        ("Flood", "flood_risk"),
        ("Wildfire", "wildfire_risk"),
    ]:
        change = _describe_change(label, baseline.get(key, "Low"), state.get(key) or "Low")
        if change:
            changes.append(change)

    if not changes:
        state["risk_trend"] = "Risk levels have been stable recently, with no major changes."
    else:
        state["risk_trend"] = "; ".join(changes) + "."

    print(f"[Forecast Agent] {state['risk_trend']}")
    return state
