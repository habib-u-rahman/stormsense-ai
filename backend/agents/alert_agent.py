# Alert agent: decides when and how to trigger disaster alerts based on analysis results

from graph.state import StormSenseState


def get_triggering_hazards(state: StormSenseState, risk_level: str) -> list[str]:
    """Return the disaster types whose individual risk matches the given risk level."""
    hazards = []
    if state.get("earthquake_risk") == risk_level:
        hazards.append("earthquake")
    if state.get("flood_risk") == risk_level:
        hazards.append("flood")
    if state.get("wildfire_risk") == risk_level:
        hazards.append("wildfire")
    return hazards


def alert_agent(state: StormSenseState) -> StormSenseState:
    """Decide whether to trigger an alert based on the overall risk level."""
    overall_risk = state.get("overall_risk")

    # Low and Medium overall risk do not require an alert
    if overall_risk in ("Low", "Medium"):
        state["alert_triggered"] = False
        state["alert_message"] = ""
        print(f"No alert needed — risk level is {overall_risk}")

    # High risk triggers a cautionary alert naming the affected hazard(s)
    elif overall_risk == "High":
        hazards = get_triggering_hazards(state, "High")
        hazard_text = " and ".join(hazards) if hazards else "one or more hazards"
        state["alert_triggered"] = True
        state["alert_message"] = (
            f"Warning: High risk of {hazard_text} has been detected in your area. "
            f"Please stay alert, monitor local updates, and be prepared to take precautions. "
            f"Avoid unnecessary travel to affected zones until conditions improve."
        )
        print("ALERT TRIGGERED — High risk detected")

    # Critical risk triggers an urgent emergency alert naming the affected hazard(s)
    elif overall_risk == "Critical":
        hazards = get_triggering_hazards(state, "Critical")
        hazard_text = " and ".join(hazards) if hazards else "one or more hazards"
        state["alert_triggered"] = True
        state["alert_message"] = (
            f"EMERGENCY: Critical risk of {hazard_text} has been detected — immediate action is required. "
            f"Evacuate or seek safe shelter right away and follow instructions from local emergency authorities. "
            f"Do not delay — this is a life-threatening situation."
        )
        print("CRITICAL ALERT TRIGGERED — Immediate action required")

    # Fallback for an unexpected or missing overall_risk value
    else:
        state["alert_triggered"] = False
        state["alert_message"] = ""
        print(f"No alert needed — risk level is {overall_risk}")

    return state
