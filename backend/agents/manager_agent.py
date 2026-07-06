# Manager agent: orchestrates the multi-agent workflow and routes tasks between agents

from graph.state import StormSenseState


def manager_agent(state: StormSenseState) -> StormSenseState:
    """Entry point of the pipeline: logs the incoming request and prepares the state for the other agents."""
    query = state.get("query")
    location = state.get("location") or "global"
    print(f"[Manager Agent] Received query: '{query}' | location: '{location}'")

    # Ensure alert_triggered has a safe default before the Alert Agent runs
    state.setdefault("alert_triggered", False)

    return state
