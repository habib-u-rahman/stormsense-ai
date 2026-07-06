# Writer agent: generates human-readable summaries and reports from analysis and alerts

import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_fireworks import ChatFireworks

from graph.state import StormSenseState

load_dotenv()

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")

# Used when the LLM call fails, so the pipeline still returns something useful
FALLBACK_EXPLANATION = (
    "We could not generate a detailed explanation right now. "
    "Please review the risk levels and alert message above and stay cautious."
)


def build_prompt(state: StormSenseState) -> str:
    """Build the natural-language prompt describing the current risk assessment for the LLM."""
    # Only include the alert message in the prompt if an alert was actually triggered
    alert_section = ""
    if state.get("alert_triggered"):
        alert_section = f"\nActive alert message: {state.get('alert_message')}"

    prompt = f"""You are a disaster safety communicator. Based on the risk assessment below, write a clear summary for a general audience.

Overall risk level: {state.get('overall_risk')}
Earthquake risk: {state.get('earthquake_risk')}
Flood risk: {state.get('flood_risk')}
Wildfire risk: {state.get('wildfire_risk')}
Risk reasoning: {state.get('risk_reasoning')}{alert_section}

Instructions:
- Write in simple, plain English with no scientific jargon.
- Keep it to a maximum of 4 sentences.
- Start the summary with the overall risk level.
- Briefly mention each disaster type (earthquake, flood, wildfire).
- End with a simple, practical recommendation for the user."""

    return prompt


def writer_agent(state: StormSenseState) -> StormSenseState:
    """Use a Fireworks-hosted LLM to turn the risk analysis into a plain-language explanation."""
    print("[Writer Agent] Generating plain-language explanation...")

    try:
        if not FIREWORKS_API_KEY:
            raise ValueError("FIREWORKS_API_KEY is not set in the environment.")

        # Initialize the Fireworks AI chat model via LangChain
        llm = ChatFireworks(
            model="accounts/fireworks/models/llama-v3p1-8b-instruct",
            fireworks_api_key=FIREWORKS_API_KEY,
            temperature=0.3,
            max_tokens=500,
        )

        prompt = build_prompt(state)

        # Send the prompt to the LLM and get back the plain-language explanation
        response = llm.invoke(
            [
                SystemMessage(content="You are a helpful disaster safety communicator."),
                HumanMessage(content=prompt),
            ]
        )
        final_explanation = response.content.strip()
        print("[Writer Agent] LLM explanation generated successfully.")

    except Exception as e:
        # Fall back to a basic static message if the LLM call fails for any reason
        print(f"[Writer Agent] Failed to generate explanation via LLM: {e}")
        final_explanation = FALLBACK_EXPLANATION

    state["final_explanation"] = final_explanation

    # Combine the alert message (when present) with the plain-language explanation
    if state.get("alert_triggered") and state.get("alert_message"):
        state["final_response"] = f"{state['alert_message']}\n\n{final_explanation}"
    else:
        state["final_response"] = final_explanation

    print("[Writer Agent] Final response assembled.")
    return state
