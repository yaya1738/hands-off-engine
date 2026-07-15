from typing import Any, Dict, List


class FactoryRuntimeHealth:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def collect(
        self,
        runtime: Dict[str, Any],
    ):
        health = {
            "cycles": runtime.get(
                "cycles",
                0,
            ),
            "errors": runtime.get(
                "errors",
                0,
            ),
            "running": runtime.get(
                "running",
                False,
            ),
        }

        self._history.append(
            health
        )

        return health

    def evaluate(
        self,
        health: Dict[str, Any],
    ):
        if not health["running"]:
            return "DOWN"

        if health["errors"] > 0:
            return "DEGRADED"

        return "HEALTHY"

    def status(
        self,
        runtime: Dict[str, Any],
    ):
        health = self.collect(
            runtime
        )

        return {
            "health": health,
            "status": self.evaluate(
                health
            ),
        }

    def history(self):
        return self._history
