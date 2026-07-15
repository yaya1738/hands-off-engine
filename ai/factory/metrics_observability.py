from typing import Any, Dict, List


class FactoryMetricsObservability:
    def __init__(self):
        self.metrics: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def record_metric(
        self,
        metric: Dict[str, Any],
    ):
        self.metrics.append(
            metric
        )

        result = {
            "recorded": True,
            "metric": metric,
        }

        self._history.append(
            result
        )

        return result

    def calculate_score(
        self,
        metrics: List[Dict[str, Any]],
    ):
        result = {
            "calculated": True,
            "score": 1,
            "count": len(metrics),
        }

        self._history.append(
            result
        )

        return result

    def get_dashboard(self):
        result = {
            "metrics": self.metrics,
            "count": len(self.metrics),
        }

        self._history.append(
            result
        )

        return result

    def detect_anomaly(
        self,
        metric: Dict[str, Any],
    ):
        result = {
            "detected": True,
            "anomaly": False,
            "metric": metric,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
