# StormSense AI

StormSense AI is a real-time natural disaster intelligence platform powered by a multi-agent AI system built with LangChain and LangGraph. It ingests live data from earthquake, weather, and wildfire sources, analyzes risk in real time, and generates human-readable alerts and reports.

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **AI Orchestration:** LangChain, LangGraph (multi-agent workflow)
- **Data Sources:** USGS (earthquakes), OpenWeather (weather/storms), NASA FIRMS (wildfires)
- **Config:** python-dotenv, Pydantic
- **Frontend:** TBD

## Multi-Agent Architecture

The system is powered by a graph of specialized agents:

- **Manager Agent** — orchestrates the workflow and routes tasks between agents
- **Data Agent** — fetches raw disaster data from external APIs
- **Analysis Agent** — interprets data to assess risk and severity
- **Alert Agent** — decides when and how to trigger alerts
- **Writer Agent** — generates human-readable summaries and reports

## Project Structure

```
stormsense-ai/
├── backend/
│   ├── agents/       # Individual agent implementations
│   ├── api/          # FastAPI routes
│   ├── graph/         # LangGraph state and workflow definitions
│   ├── prompts/       # Prompt templates for each agent
│   ├── tools/         # External API integrations (USGS, weather, FIRMS)
│   ├── main.py        # FastAPI application entry point
│   ├── requirements.txt
│   └── .env.example
├── frontend/          # Frontend application (coming soon)
├── .gitignore
└── README.md
```

## How to Run

### Prerequisites

- Python 3.10+
- API keys for OpenAI/Fireworks, OpenWeather, and NASA FIRMS

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/habib-u-rahman/stormsense-ai.git
   cd stormsense-ai/backend
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Then fill in your API keys in .env
   ```

4. Run the backend server:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`.

## Data Sources

| Source | Data Type | API |
|---|---|---|
| USGS | Earthquake events | [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/) |
| OpenWeather | Weather and storm data | [OpenWeather API](https://openweathermap.org/api) |
| NASA FIRMS | Wildfire hotspot data | [NASA FIRMS API](https://firms.modaps.eosdis.nasa.gov/api/) |

## Status

🚧 Hackathon project — under active development.
