# List of people who asked to receive real disaster alert emails, with no
# signup/login required — just an email address. Persisted to a small local
# JSON file so a backend restart (including uvicorn --reload picking up a
# code change) doesn't silently lose everyone who subscribed; a real product
# would use a database, but that's out of scope for the hackathon timeline.

import json
import re
from pathlib import Path
from typing import List
from typing_extensions import TypedDict

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "subscribers.json"


class Subscriber(TypedDict):
    type: str  # always "email"
    value: str


def _load() -> List[Subscriber]:
    if not _STORE_PATH.exists():
        return []
    try:
        with open(_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(subscribers: List[Subscriber]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(subscribers, f, indent=2)


_subscribers: List[Subscriber] = _load()


def add_subscriber(value: str) -> None:
    """Validate and store a new email subscriber. Raises ValueError on bad input."""
    value = value.strip()

    if not EMAIL_PATTERN.match(value):
        raise ValueError("That doesn't look like a valid email address.")

    # Avoid duplicate subscriptions
    if any(s["value"] == value for s in _subscribers):
        return

    _subscribers.append({"type": "email", "value": value})
    _save(_subscribers)
    print(f"[Subscribers] New subscriber added ({len(_subscribers)} total).")


def get_subscribers() -> List[Subscriber]:
    """Return all email subscribers."""
    return list(_subscribers)


def get_subscriber_count() -> int:
    return len(_subscribers)
