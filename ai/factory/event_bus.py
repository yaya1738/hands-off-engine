from typing import Any, Callable, Dict, List


class FactoryEventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: List[Dict[str, Any]] = []

    def subscribe(
        self,
        event_type: str,
        handler: Callable,
    ) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(
            handler
        )

    def publish(
        self,
        event_type: str,
        payload: Any = None,
    ):
        event = {
            "event": event_type,
            "payload": payload,
        }

        self._history.append(event)

        results = []

        for handler in self._subscribers.get(
            event_type,
            [],
        ):
            results.append(
                handler(payload)
            )

        return results

    def history(self):
        return self._history
