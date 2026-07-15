from typing import Any, Callable, Dict, List


class FactoryEventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.events: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def subscribe(
        self,
        event_type: str,
        handler: Callable,
    ):
        self.subscribers.setdefault(
            event_type,
            [],
        ).append(handler)

        result = {
            "subscribed": True,
            "event_type": event_type,
        }

        self._history.append(result)

        return result

    def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ):
        event = {
            "type": event_type,
            "payload": payload,
        }

        self.events.append(event)

        for handler in self.subscribers.get(event_type, []):
            handler(payload)

        result = {
            "published": True,
            "event": event,
        }

        self._history.append(result)

        return result

    def emit_runtime_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ):
        return self.publish_event(
            event_type,
            payload,
        )

    def process_events(self):
        result = {
            "processed": True,
            "count": len(self.events),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
