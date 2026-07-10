# StormSense AI

StormSense AI is a real-time natural disaster intelligence platform powered by a multi-agent AI system built with LangChain and LangGraph. It ingests live data from earthquake, weather, and wildfire sources, analyzes risk in real time, and generates human-readable alerts and reports.

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **AI Orchestration:** LangChain, LangGraph (multi-agent workflow)
- **LLM:** Groq (`llama-3.1-8b-instant`)
- **Data Sources:** USGS (earthquakes), OpenWeather (weather/storms), NASA FIRMS (wildfires)
- **Config:** python-dotenv, Pydantic
- **Frontend:** Next.js (App Router, TypeScript), Tailwind CSS, react-leaflet, framer-motion

## Multi-Agent Architecture

The system is powered by a graph of specialized agents:

- **Manager Agent** — orchestrates the workflow and routes tasks between agents
- **Data Agent** — fetches raw disaster data from external APIs
- **Analysis Agent** — interprets data to assess risk and severity
- **Alert Agent** — decides when and how to trigger alerts
- **Forecast Agent** — compares current risk against recent history to describe whether it's rising, easing, or stable
- **Writer Agent** — generates human-readable summaries and reports
- **Notifier Agent** — sends a real email when the autonomous monitor (not chat) detects a High/Critical alert

## Project Structure

```
stormsense-ai/
├── backend/
│   ├── agents/             # Individual agent implementations
│   ├── api/                # FastAPI routes
│   ├── graph/               # LangGraph state and workflow definitions
│   ├── prompts/              # Prompt templates for each agent
│   ├── tools/                 # Raw-API-response parsers (USGS, weather, FIRMS)
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt
│   └── .env.example
├── stormsense-frontend/       # Next.js dashboard (map, chat, live risk cards)
│   └── app/
│       ├── lib/api.ts          # Backend API client
│       ├── components/          # DisasterMap (Leaflet)
│       └── page.tsx              # Main dashboard
├── .gitignore
└── README.md
```

## How to Run

### Prerequisites

- Python 3.10+
- Node.js 18+
- API keys for Groq, OpenWeather, and NASA FIRMS

### Backend

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

The API will be available at `http://localhost:8000` (interactive docs at `/docs`).

### Frontend

```bash
cd stormsense-frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The dashboard talks to the backend through a Next.js rewrite proxy (`next.config.ts`), so the backend must be running on port 8000 for the map, risk cards, alerts, and chat to show live data.

## Data Sources

| Source | Data Type | API |
|---|---|---|
| USGS | Earthquake events | [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/) |
| OpenWeather | Weather and storm data | [OpenWeather API](https://openweathermap.org/api) |
| NASA FIRMS | Wildfire hotspot data | [NASA FIRMS API](https://firms.modaps.eosdis.nasa.gov/api/) |

## Status

Backend pipeline and frontend dashboard are both live and connected end-to-end: the map, risk score cards, real-time alerts, and chat all run on real data from the 7-agent pipeline. 🚧 Hackathon project — under active development.
