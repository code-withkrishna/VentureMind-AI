"""Pendo server-side Track Event utility using the Pendo Track API."""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

PENDO_DATA_HOST = "https://data.pendo.io"
PENDO_INTEGRATION_KEY = "976d716a-f2e2-46c6-b542-8dc1566311d8"


def pendo_track(
    event: str,
    properties: dict[str, Any] | None = None,
    visitor_id: str = "system",
    account_id: str = "system",
) -> None:
    """Send a Track Event to the Pendo Track API (fire-and-forget in a thread)."""
    payload = {
        "type": "track",
        "event": event,
        "visitorId": visitor_id,
        "accountId": account_id,
        "timestamp": int(time.time() * 1000),
        "properties": properties or {},
    }
    # Fire-and-forget so tracking never blocks the pipeline
    threading.Thread(target=_send, args=(payload,), daemon=True).start()


def _send(payload: dict[str, Any]) -> None:
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{PENDO_DATA_HOST}/data/track",
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-pendo-integration-key": PENDO_INTEGRATION_KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read()
    except Exception:
        logger.debug("Pendo track event failed for '%s'", payload.get("event"), exc_info=True)
