from typing import Any, Dict, List


class FactoryEventIntelligence:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.subscribers: Dict[str, List[str]] = {}
        self._history: List[Dict[str, Any]] = []

    def publish_event(
        self,
        event: Dict[str, Any],
    ):
        self.events.append(event)

        result = {
            "published": True,
            "event": event,
        }

        self._history.append(result)

        return result

    def subscribe(
        self,
        event_type: str,
        subscriber: str,
    ):
        self.subscribers.setdefault(
            event_type,
            []
        ).append(subscriber)

        result = {
            "subscribed": True,
            "event_type": event_type,
            "subscriber": subscriber,
        }

        self._history.append(result)

        return result

    def process_events(self):
        result = {
            "processed": True,
            "count": len(self.events),
        }

        self._history.append(result)

        return result

    def route_event(
        self,
        event_type: str,
    ):
        result = {
            "routed": True,
            "event_type": event_type,
            "targets": self.subscribers.get(
                event_type,
                []
            ),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
