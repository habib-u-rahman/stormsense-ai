# Workflow: builds and compiles the LangGraph multi-agent graph
# (manager -> data -> analysis -> alert -> forecast -> writer -> notifier)

from langgraph.graph import StateGraph, END

from agents.manager_agent import manager_agent
from agents.data_agent import data_agent
from agents.analysis_agent import analysis_agent
from agents.alert_agent import alert_agent
from agents.forecast_agent import forecast_agent
from agents.writer_agent import writer_agent
from agents.notifier_agent import notifier_agent
from graph.state import StormSenseState

# Build the graph using StormSenseState as the shared schema passed between all nodes
graph = StateGraph(StormSenseState)

# Register each agent function as a node in the graph
graph.add_node("manager", manager_agent)
graph.add_node("data", data_agent)
graph.add_node("analysis", analysis_agent)
graph.add_node("alert", alert_agent)
graph.add_node("forecast", forecast_agent)
graph.add_node("writer", writer_agent)
graph.add_node("notifier", notifier_agent)

# Define the linear pipeline flow:
# manager -> data -> analysis -> alert -> forecast -> writer -> notifier -> END
graph.add_edge("manager", "data")
graph.add_edge("data", "analysis")
graph.add_edge("analysis", "alert")
graph.add_edge("alert", "forecast")
graph.add_edge("forecast", "writer")
graph.add_edge("writer", "notifier")
graph.add_edge("notifier", END)

# The manager agent is where every run of the pipeline begins
graph.set_entry_point("manager")

# Compile the graph into a runnable workflow
workflow = graph.compile()


def run_pipeline(query: str, location: str = "", autonomous: bool = False) -> StormSenseState:
    """Run the full StormSense AI pipeline for a given query/location and return the final state.

    `autonomous` must only be True for scheduled background runs (the
    autonomous monitor) — it's what allows the Notifier Agent to send a real
    email. User-initiated chat queries must never set this, or asking a
    question could trigger a real-world notification.
    """
    # Seed the shared state with the initial query and location; every other field
    # gets filled in as the state flows through the manager, data, analysis, alert, writer, and notifier agents
    initial_state: StormSenseState = {
        "query": query,
        "location": location,
        "autonomous": autonomous,
    }

    final_state = workflow.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    result = run_pipeline(
        query="What is the current disaster risk?",
        location="Pakistan",
    )
    print(result["final_response"])
