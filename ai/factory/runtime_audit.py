from typing import Any, Dict, List


class FactoryRuntimeAudit:
    def __init__(self):
        self._events: List[Dict[str, Any]] = []

    def record(
        self,
        event_type: str,
        data: Dict[str, Any],
    ):
        event = {
            "type": event_type,
            "data": data,
        }

        self._events.append(
            event
        )

        return event

    def query(
        self,
        event_type: str,
    ):
        return [
            event
            for event in self._events
            if event["type"] == event_type
        ]

    def export(self):
        return self._events

    def history(self):
        return self._events
