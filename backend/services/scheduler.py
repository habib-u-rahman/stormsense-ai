# Autonomous monitor: periodically re-runs the full 7-agent pipeline in the
# background and broadcasts live updates to connected dashboard clients, so
# StormSense keeps watching even when nobody is actively asking it anything.
# This is what makes it an autonomous monitor rather than a request/response
# chatbot.

import asyncio
import os

from api.routes import run_analysis_and_shape
from api.websocket import broadcast
from services.history import record_snapshot

# How often the autonomous monitor re-checks global risk. Kept comfortably
# under NASA FIRMS' 5000-transactions-per-10-minutes limit while still
# feeling "live" for a demo.
POLL_INTERVAL_SECONDS = int(os.getenv("AUTONOMOUS_POLL_INTERVAL_SECONDS", "180"))

# Hard ceiling on a single cycle (data fetches + LLM + email sends). No
# matter what's slow or stuck — a hung SMTP connection, a network stall
# anywhere — the loop is GUARANTEED to give up and move on to the next
# cycle rather than freezing forever. This is the actual fix for "it only
# updates once": the underlying cause doesn't matter if nothing can block
# past this ceiling.
CYCLE_TIMEOUT_SECONDS = 90

AUTONOMOUS_QUERY = "Global disaster risk overview"


def _run_pipeline_sync() -> dict:
    """Run the pipeline synchronously and return a JSON-serializable snapshot."""
    # autonomous=True is what allows the Notifier Agent to send a real
    # email for this run — only the scheduler should ever pass this.
    response = run_analysis_and_shape(AUTONOMOUS_QUERY, "", autonomous=True)
    return response.model_dump()


async def _run_one_cycle() -> None:
    """Run a single check-and-broadcast cycle."""
    print("[Autonomous Monitor] Running scheduled global risk check...")
    # run_analysis_and_shape is sync and makes real network calls, so it's
    # run in a worker thread — otherwise it would block the entire FastAPI
    # event loop (including the WebSocket and every other HTTP request)
    # for the ~20s the pipeline takes.
    snapshot = await asyncio.to_thread(_run_pipeline_sync)
    record_snapshot(snapshot)
    await broadcast(snapshot)
    print(f"[Autonomous Monitor] Overall risk: {snapshot.get('overall_risk')}.")


async def autonomous_monitor_loop() -> None:
    """Run forever: re-check global risk on a fixed interval and broadcast updates."""
    print(f"[Autonomous Monitor] Started — checking every {POLL_INTERVAL_SECONDS}s.")

    while True:
        try:
            await asyncio.wait_for(_run_one_cycle(), timeout=CYCLE_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            print(f"[Autonomous Monitor] Cycle exceeded {CYCLE_TIMEOUT_SECONDS}s — abandoning it and continuing.")
        except Exception as e:
            print(f"[Autonomous Monitor] Scheduled check failed: {e}")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)
