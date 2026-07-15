from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryHealthSnapshot:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def collect(
        self,
        components: Dict[str, Any],
    ):
        issues = [
            name
            for name, state in components.items()
            if state != "HEALTHY"
        ]

        snapshot = {
            "health": (
                "HEALTHY"
                if not issues
                else "DEGRADED"
            ),
            "components": len(components),
            "issues": issues,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._history.append(snapshot)

        return snapshot

    def status(
        self,
        components,
    ):
        return self.collect(
            components
        )["health"]

    def snapshot(self):
        return (
            self._history[-1]
            if self._history
            else {}
        )

    def history(self):
        return self._history
