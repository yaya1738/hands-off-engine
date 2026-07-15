from typing import Any, Dict, List


class FactoryImprovementMetrics:
    def __init__(self):
        self._metrics: List[Dict[str, Any]] = []

    def record_metric(
        self,
        metric: Dict[str, Any],
    ):
        self._metrics.append(
            metric
        )

        return metric

    def calculate(self):
        if not self._metrics:
            return {
                "count": 0,
                "success_rate": 0,
                "average_impact": 0,
            }

        successes = [
            metric
            for metric in self._metrics
            if metric.get(
                "success",
                False,
            )
        ]

        impacts = [
            metric.get(
                "impact",
                0,
            )
            for metric in self._metrics
        ]

        return {
            "count": len(
                self._metrics
            ),
            "success_rate": (
                len(successes)
                / len(self._metrics)
            ),
            "average_impact": (
                sum(impacts)
                / len(impacts)
            ),
        }

    def summary(self):
        return self.calculate()

    def history(self):
        return self._metrics
