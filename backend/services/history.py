# In-memory rolling history of past autonomous risk-check snapshots. Powers
# the dashboard's trend chart and the Forecast Agent's trend reasoning.
# Resets on backend restart — this is a live-demo convenience, not meant as
# a permanent data store (no database needed for the hackathon timeline).

from datetime import datetime, timezone
from typing import List
from typing_extensions import TypedDict

# ~10 hours of history at the default 3-minute autonomous poll interval
MAX_HISTORY_ENTRIES = 200


class HistoryEntry(TypedDict):
    timestamp: str
    overall_risk: str
    earthquake_risk: str
    flood_risk: str
    wildfire_risk: str


_history: List[HistoryEntry] = []


def record_snapshot(snapshot: dict) -> None:
    """Append a new risk snapshot to the rolling history, trimming old entries."""
    entry: HistoryEntry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_risk": snapshot.get("overall_risk") or "Low",
        "earthquake_risk": snapshot.get("earthquake_risk") or "Low",
        "flood_risk": snapshot.get("flood_risk") or "Low",
        "wildfire_risk": snapshot.get("wildfire_risk") or "Low",
    }
    _history.append(entry)
    if len(_history) > MAX_HISTORY_ENTRIES:
        del _history[0]


def get_history() -> List[HistoryEntry]:
    """Return the full rolling history, oldest first."""
    return list(_history)
