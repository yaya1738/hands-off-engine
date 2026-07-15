from typing import Dict, Any


class FactoryTelemetry:
    def __init__(self):
        self._events = []

    def record(self, event: Dict[str, Any]) -> None:
        self._events.append(event)

    def stats(self) -> Dict[str, int]:
        success = sum(
            1
            for event in self._events
            if event.get("status") == "SUCCESS"
        )

        failed = sum(
            1
            for event in self._events
            if event.get("status") == "FAILED"
        )

        return {
            "total": len(self._events),
            "success": success,
            "failed": failed,
        }
