"""Simple event listener to trigger alerts from SOC components."""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from .notifier import Notifier


class AlertService:
    """Listen for events and send contextual alerts."""

    def __init__(self, notifier: Notifier) -> None:
        self.notifier = notifier

    def handle_event(self, source: str, event_type: str, host: str) -> Dict[str, str]:
        """Process an event and dispatch an alert."""
        event = {
            "source": source,
            "type": event_type,
            "host": host,
            "timestamp": datetime.utcnow().isoformat(),
        }
        message = (
            f"[{event['timestamp']}] {event['source']} detected "
            f"{event['type']} on {event['host']}"
        )
        self.notifier.send(message)
        return event
