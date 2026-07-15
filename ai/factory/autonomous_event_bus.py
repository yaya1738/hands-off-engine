from typing import Any, Callable, Dict, List


class FactoryAutonomousEventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.events: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def publish(
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
        handler: Callable,
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

    def dispatch(
        self,
        event: Dict[str, Any],
    ):
        handlers = self.subscribers.get(
            event.get("type"),
            []
        )

        for handler in handlers:
            handler(event)

        result = {
            "dispatched": True,
            "handlers": len(
                handlers
            ),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
