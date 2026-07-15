from typing import Any, Dict, List


class FactoryRuntimeObservability:
    def __init__(self):
        self.metrics: List[Dict[str, Any]] = []
        self.health_checks: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def record_metric(
        self,
        metric: Dict[str, Any],
    ):
        self.metrics.append(metric)

        result = {
            "recorded": True,
            "metric": metric,
        }

        self._history.append(result)

        return result

    def capture_health(
        self,
        health: Dict[str, Any],
    ):
        self.health_checks.append(health)

        result = {
            "captured": True,
            "health": health,
        }

        self._history.append(result)

        return result

    def detect_anomaly(
        self,
        data: Dict[str, Any],
    ):
        result = {
            "detected": True,
            "data": data,
        }

        self._history.append(result)

        return result

    def generate_alert(
        self,
        alert: Dict[str, Any],
    ):
        self.alerts.append(alert)

        result = {
            "generated": True,
            "alert": alert,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
