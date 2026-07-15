from typing import Any, Dict, List


class FactoryResilienceController:
    def __init__(
        self,
        health=None,
        alerts=None,
        recovery=None,
    ):
        self.health = health
        self.alerts = alerts
        self.recovery = recovery
        self._history: List[Dict[str, Any]] = []

    def evaluate(
        self,
        runtime: Dict[str, Any],
    ):
        health_result = self.health.status(
            runtime
        )

        alert = self.alerts.check(
            health_result
        )

        result = {
            "health": health_result,
            "alert": alert,
        }

        self._history.append(
            result
        )

        return result

    def respond(
        self,
        evaluation: Dict[str, Any],
    ):
        alert = evaluation.get(
            "alert",
            {},
        )

        result = self.recovery.recover(
            alert
        )

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
