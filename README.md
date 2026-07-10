# StormSense AI

StormSense AI is a real-time natural disaster intelligence platform powered by a 7-agent AI system built with LangChain and LangGraph. It ingests live data from earthquake, weather, and wildfire sources, analyzes risk in real time, tracks how that risk is trending, and autonomously alerts subscribers by email — all without anyone needing to ask it anything.

## Key Features

- **Truly autonomous, not just a chatbot.** A background monitor re-checks global risk on a fixed interval (every 3 minutes by default) independent of any user request, and pushes live updates to the dashboard over WebSocket — no page refresh, no polling.
- **Real email alerts, no login required.** Anyone can subscribe their email address from the dashboard; when the autonomous monitor detects High/Critical risk, real emails go out automatically (with cooldown logic so an ongoing crisis doesn't spam).
- **Risk trend over time.** A live chart shows how overall risk has moved recently, and a Forecast Agent describes it in plain language (e.g. "wildfire risk has risen from Medium to Critical").
- **Live interactive map** (Leaflet) plotting real earthquake, wildfire, and weather events with per-event risk coloring.
- **Conversational chat** that answers the specific question asked — using real, current data — instead of a canned summary, and supports optional location scoping.

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, WebSockets
- **AI Orchestration:** LangChain, LangGraph (7-agent workflow)
- **LLM:** Groq (`llama-3.1-8b-instant`)
- **Data Sources:** USGS (earthquakes), OpenWeather (weather/storms), NASA FIRMS (wildfires)
- **Alerts:** SMTP (email)
- **Config:** python-dotenv, Pydantic
- **Frontend:** Next.js (App Router, TypeScript), Tailwind CSS, react-leaflet, framer-motion

## Multi-Agent Architecture

The system is powered by a graph of 7 specialized agents:

```
Manager → Data → Analysis → Alert → Forecast → Writer → Notifier
```

- **Manager Agent** — entry point of every run; logs and validates the incoming request
- **Data Agent** — fetches live raw disaster data from USGS, OpenWeatherMap, and NASA FIRMS (in parallel, with per-source timeouts so one slow source can't stall the rest)
- **Analysis Agent** — classifies risk (Low/Medium/High/Critical) per hazard and overall
- **Alert Agent** — decides whether the situation warrants an alert and drafts the message
- **Forecast Agent** — compares current risk against recent history to describe the trend
- **Writer Agent** — turns the technical assessment into a plain-language answer tailored to what was actually asked
- **Notifier Agent** — sends a real email to subscribers when an autonomous (not chat) run detects a High/Critical alert

Every run flows through all 7 agents. The only thing that differs between a chat question and the autonomous monitor is one flag (`autonomous: bool`) — it's what gates the Notifier Agent's real-world side effect, so asking the chatbot a question can never accidentally trigger a real email.

## Project Structure

```
stormsense-ai/
├── backend/
│   ├── agents/                 # The 7 agents (manager, data, analysis, alert, forecast, writer, notifier)
│   ├── api/
│   │   ├── routes.py            # REST endpoints (/api/analyze, /api/history, /api/subscribe, ...)
│   │   └── websocket.py          # /ws/live — pushes live snapshots to connected dashboards
│   ├── graph/                   # LangGraph state schema and workflow wiring
│   ├── prompts/                  # Prompt templates for each agent
│   ├── services/
│   │   ├── scheduler.py           # Autonomous background monitor loop
│   │   ├── history.py              # Rolling risk history (powers the trend chart)
│   │   └── subscribers.py          # No-login email subscription list (persisted locally, gitignored)
│   ├── tools/                    # Raw-API-response parsers (USGS, weather, FIRMS)
│   ├── data/                     # Local persisted state (subscribers.json) — gitignored
│   ├── main.py                    # FastAPI app + autonomous monitor startup
│   ├── requirements.txt
│   └── .env.example
├── stormsense-frontend/          # Next.js dashboard
│   └── app/
│       ├── lib/api.ts              # Backend API client (REST + WebSocket)
│       ├── components/              # DisasterMap, RiskTrendChart, SubscribeForm
│       └── page.tsx                  # Main dashboard
├── .gitignore
└── README.md
```

## How to Run

### Prerequisites

- Python 3.10+
- Node.js 18+
- API keys for Groq, OpenWeather, and NASA FIRMS (all free tier)
- Optional: a Gmail account + [App Password](https://myaccount.google.com/apppasswords) if you want real email alerts to actually send

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
   # Fill in GROQ_API_KEY, OPENWEATHER_API_KEY, NASA_FIRMS_API_KEY
   # SMTP_* is optional — leave blank to skip real email sending
   ```

4. Run the backend server:
   ```bash
   uvicorn main:app --reload
   ```

The API is available at `http://localhost:8000` (interactive docs at `/docs`). On startup, the autonomous monitor begins running in the background automatically — check the terminal for `[Autonomous Monitor] Started`.

### Frontend

```bash
cd stormsense-frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The dashboard talks to the backend through a Next.js rewrite proxy (`next.config.ts`) for REST calls, and connects directly to `ws://localhost:8000/ws/live` for live push updates — the backend must be running on port 8000 for the map, risk cards, alerts, trend chart, and chat to show live data.

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/analyze` | POST | Run the full pipeline for a chat query (`query`, optional `location`) |
| `/api/trigger-check` | POST | Manually force one autonomous cycle right now, instead of waiting for the schedule |
| `/api/history` | GET | Rolling history of past risk snapshots, for the trend chart |
| `/api/subscribe` | POST | Register an email (`value`) to receive real alerts — no login |
| `/api/health` | GET | Health check |
| `/ws/live` | WebSocket | Live push feed — sends a snapshot on connect, then on every autonomous cycle |

## Data Sources

| Source | Data Type | API |
|---|---|---|
| USGS | Earthquake events | [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/) |
| OpenWeather | Weather and storm data | [OpenWeather API](https://openweathermap.org/api) |
| NASA FIRMS | Wildfire hotspot data | [NASA FIRMS API](https://firms.modaps.eosdis.nasa.gov/api/) |

## Status

Backend and frontend are fully connected end-to-end and verified live: the map, risk score cards, real-time alerts, trend chart, chat, and email subscriptions all run on real data from the 7-agent pipeline, with the autonomous monitor running continuously in the background. 🚧 Hackathon project — built for the AMD Developer Hackathon.
