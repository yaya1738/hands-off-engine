from typing import Any, Dict, List


class FactoryRuntimeAlerts:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def check(
        self,
        health: Dict[str, Any],
    ):
        status = health.get(
            "status"
        )

        if status == "DOWN":
            return self.alert(
                "CRITICAL",
                "runtime down",
            )

        if status == "DEGRADED":
            return self.alert(
                "WARNING",
                "runtime degraded",
            )

        return self.alert(
            "INFO",
            "runtime healthy",
        )

    def alert(
        self,
        level: str,
        reason: str,
    ):
        result = {
            "level": level,
            "reason": reason,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
