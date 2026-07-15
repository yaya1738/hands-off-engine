from typing import Any, Dict, List


class FactoryHealthMonitor:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def collect(
        self,
        snapshot: Dict[str, Any],
    ):
        self._history.append(
            snapshot
        )

        return snapshot

    def compare(
        self,
        previous: Dict[str, Any],
        current: Dict[str, Any],
    ):
        previous_health = previous.get(
            "health"
        )

        current_health = current.get(
            "health"
        )

        return {
            "previous": previous_health,
            "current": current_health,
            "changed": (
                previous_health
                != current_health
            ),
        }

    def detect_change(self):
        if len(self._history) < 2:
            return {
                "changed": False,
            }

        return self.compare(
            self._history[-2],
            self._history[-1],
        )

    def history(self):
        return self._history
