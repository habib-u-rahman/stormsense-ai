# Writer agent: generates human-readable summaries and reports from analysis and alerts

import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from graph.state import StormSenseState
from prompts.writer_prompt import WRITER_PROMPT

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Used when the LLM call fails, so the pipeline still returns something useful
FALLBACK_EXPLANATION = (
    "We could not generate a detailed explanation right now. "
    "Please review the risk levels and alert message above and stay cautious."
)


def _describe_current_weather(raw_weather_data: dict | None) -> str | None:
    """Pull a plain-language weather snapshot out of the raw OpenWeatherMap response, if available."""
    if not raw_weather_data:
        return None

    weather_list = raw_weather_data.get("weather") or []
    condition = weather_list[0].get("description") if weather_list else None
    main = raw_weather_data.get("main") or {}
    temp = main.get("temp")
    humidity = main.get("humidity")
    wind = (raw_weather_data.get("wind") or {}).get("speed")
    city = raw_weather_data.get("name")

    if condition is None and temp is None:
        return None

    parts = [f"Weather snapshot for {city or 'the requested location'}: {condition or 'conditions unavailable'}"]
    if temp is not None:
        parts.append(f"{temp}°C")
    if humidity is not None:
        parts.append(f"{humidity}% humidity")
    if wind is not None:
        parts.append(f"wind {wind} m/s")
    return ", ".join(parts) + "."


def build_prompt(state: StormSenseState) -> str:
    """Build the natural-language prompt describing the current risk assessment for the LLM."""
    # Only include the alert message in the prompt if an alert was actually triggered
    alert_section = ""
    if state.get("alert_triggered"):
        alert_section = f"\nActive alert message: {state.get('alert_message')}"

    query = state.get("query") or "What is the current disaster risk?"
    location = state.get("location")
    location_line = (
        f"Location focus: {location} (weather/flood data below is for this location; "
        f"earthquake/wildfire data is global, not specific to it)"
        if location
        else "Location focus: none given — all data below is global. "
        "If the user asked about a specific place, tell them you don't have location-specific "
        "data unless they provide a location, and answer with the global data instead."
    )

    weather_snapshot = _describe_current_weather(state.get("raw_weather_data"))
    weather_section = f"\n{weather_snapshot}" if weather_snapshot else ""

    risk_trend = state.get("risk_trend")
    trend_section = f"\nRecent trend: {risk_trend}" if risk_trend else ""

    prompt = f"""A user asked: "{query}"

Answer their question directly using the real-time risk assessment below. Never claim data is specific to a location unless the location focus below actually names that location.

{location_line}
Overall risk level: {state.get('overall_risk')}
Earthquake risk: {state.get('earthquake_risk')}
Flood risk: {state.get('flood_risk')}
Wildfire risk: {state.get('wildfire_risk')}
Risk reasoning: {state.get('risk_reasoning')}{weather_section}{trend_section}{alert_section}

Instructions:
- Answer the user's actual question directly and specifically. If they asked about current weather/temperature/conditions, use the weather snapshot above if provided.
- If they asked about one hazard (e.g. just earthquakes), focus on that hazard first.
- If they asked whether risk is rising, falling, or changing, use the recent trend above if provided — otherwise don't bring up trend at all.
- Write in simple, plain English with no scientific jargon.
- Keep it to a maximum of 4 sentences.
- Only bring up hazards they didn't ask about if the overall situation is High or Critical and they should know.
- Do not wrap your answer in quotation marks.
- End with a simple, practical recommendation for the user."""

    return prompt


def writer_agent(state: StormSenseState) -> StormSenseState:
    """Use a Groq-hosted LLM to turn the risk analysis into a plain-language explanation."""
    print("[Writer Agent] Generating plain-language explanation...")

    try:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in the environment.")

        # Initialize the Groq chat model via LangChain
        llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=500,
            timeout=20,
        )

        prompt = build_prompt(state)

        # Send the prompt to the LLM and get back the plain-language explanation
        response = llm.invoke(
            [
                SystemMessage(content=WRITER_PROMPT),
                HumanMessage(content=prompt),
            ]
        )
        # Groq occasionally wraps the whole answer in quote marks despite being told not to
        final_explanation = response.content.strip().strip('"').strip("'").strip()
        print("[Writer Agent] LLM explanation generated successfully.")

    except Exception as e:
        # Fall back to a basic static message if the LLM call fails for any reason
        print(f"[Writer Agent] Failed to generate explanation via LLM: {e}")
        final_explanation = FALLBACK_EXPLANATION

    state["final_explanation"] = final_explanation

    # Only staple the raw EMERGENCY banner onto autonomous runs (the
    # dashboard's background monitor) — a chat query already gets alert
    # context baked into its tailored answer via the prompt, so repeating
    # the generic banner on every single chat response is just noise that
    # doesn't reflect what the user actually asked.
    if state.get("autonomous") and state.get("alert_triggered") and state.get("alert_message"):
        state["final_response"] = f"{state['alert_message']}\n\n{final_explanation}"
    else:
        state["final_response"] = final_explanation

    print("[Writer Agent] Final response assembled.")
    return state
