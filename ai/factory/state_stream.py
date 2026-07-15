from typing import Any, Callable, Dict, List


class FactoryStateStream:
    def __init__(self):
        self._latest: Dict[str, Any] = {}
        self._subscribers: List[Callable] = []

    def publish_state(
        self,
        state: Dict[str, Any],
    ) -> None:
        self._latest = state

        for subscriber in self._subscribers:
            subscriber(state)

    def subscribe(
        self,
        handler: Callable,
    ) -> None:
        self._subscribers.append(handler)

    def latest(self):
        return self._latest
