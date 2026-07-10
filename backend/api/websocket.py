# WebSocket endpoint: pushes live pipeline snapshots to connected dashboard
# clients as they happen, so the frontend doesn't need to poll for updates.

import asyncio
from typing import Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# A send that never gets acknowledged (e.g. a browser tab closed abruptly,
# without a clean WebSocket close handshake) can otherwise hang forever —
# and since broadcast() is called from the single autonomous monitor loop,
# one stuck client would silently freeze all future scheduled checks.
SEND_TIMEOUT_SECONDS = 5

_active_connections: Set[WebSocket] = set()

# The most recent snapshot broadcast by the autonomous monitor, so a client
# connecting between scheduled runs still gets something immediately instead
# of waiting for the next cycle.
_latest_snapshot: Optional[dict] = None


@router.websocket("/ws/live")
async def live_updates(websocket: WebSocket):
    """Accept a dashboard client, send the latest known snapshot, then stream live updates."""
    await websocket.accept()
    _active_connections.add(websocket)
    print(f"[WebSocket] Client connected ({len(_active_connections)} active).")

    try:
        if _latest_snapshot is not None:
            await asyncio.wait_for(websocket.send_json(_latest_snapshot), timeout=SEND_TIMEOUT_SECONDS)

        # We don't expect messages from the client — awaiting receive() just
        # lets us detect disconnects promptly instead of leaving a dead entry
        # in _active_connections until the next broadcast fails.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WebSocket] Error on client connection: {e}")
    finally:
        _active_connections.discard(websocket)
        print(f"[WebSocket] Client disconnected ({len(_active_connections)} active).")


async def broadcast(snapshot: dict) -> None:
    """Push a new snapshot to every connected dashboard client.

    Each send is individually timed out so one unresponsive connection can
    never block the others — or worse, freeze the autonomous monitor loop
    that calls this, since that loop only ever runs one broadcast at a time.
    """
    global _latest_snapshot
    _latest_snapshot = snapshot

    dead_connections = set()
    for connection in list(_active_connections):
        try:
            await asyncio.wait_for(connection.send_json(snapshot), timeout=SEND_TIMEOUT_SECONDS)
        except Exception as e:
            print(f"[WebSocket] Dropping unresponsive client: {e}")
            dead_connections.add(connection)

    _active_connections.difference_update(dead_connections)
    print(f"[WebSocket] Broadcast sent to {len(_active_connections)} client(s).")
