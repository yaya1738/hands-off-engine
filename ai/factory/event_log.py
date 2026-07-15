from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryEventLog:
    def __init__(self):
        self._events: List[Dict[str, Any]] = []

    def record(self, event_type: str, data: Dict[str, Any]) -> None:
        self._events.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "data": data,
            }
        )

    def all(self) -> List[Dict[str, Any]]:
        return self._events
