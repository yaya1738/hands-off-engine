from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryAuditLog:
    def __init__(self):
        self._events: List[Dict[str, Any]] = []

    def record_event(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._events.append(event)

        return event

    def list_events(self):
        return self._events

    def filter_events(
        self,
        event_type: str,
    ):
        return [
            event
            for event in self._events
            if event["type"] == event_type
        ]
