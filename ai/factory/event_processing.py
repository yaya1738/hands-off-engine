from typing import Any, Dict, List


class FactoryEventProcessing:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.subscribers: Dict[str, List[Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def publish_event(
        self,
        event: Dict[str, Any],
    ):
        self.events.append(
            event
        )

        result = {
            "published": True,
            "event": event,
        }

        self._history.append(
            result
        )

        return result

    def subscribe(
        self,
        event_type: str,
        handler: Any,
    ):
        self.subscribers.setdefault(
            event_type,
            []
        ).append(
            handler
        )

        result = {
            "subscribed": True,
            "event_type": event_type,
        }

        self._history.append(
            result
        )

        return result

    def process_events(self):
        result = {
            "processed": True,
            "count": len(
                self.events
            ),
        }

        self._history.append(
            result
        )

        return result

    def clear_events(self):
        count = len(
            self.events
        )

        self.events.clear()

        result = {
            "cleared": True,
            "count": count,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
