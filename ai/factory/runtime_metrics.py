from typing import Any, Dict, List


class FactoryRuntimeMetrics:
    def __init__(self):
        self.metrics: Dict[str, int] = {
            "cycles": 0,
            "successes": 0,
            "failures": 0,
        }
        self._history: List[Dict[str, Any]] = []

    def increment(
        self,
        metric: str,
        amount: int = 1,
    ):
        self.metrics[metric] = (
            self.metrics.get(metric, 0)
            + amount
        )

        result = {
            metric: self.metrics[metric],
        }

        self._history.append(
            result
        )

        return result

    def record(
        self,
        success: bool,
    ):
        self.increment(
            "cycles"
        )

        if success:
            self.increment(
                "successes"
            )

        else:
            self.increment(
                "failures"
            )

        result = {
            "recorded": True,
            "metrics": self.metrics.copy(),
        }

        self._history.append(
            result
        )

        return result

    def snapshot(self):
        result = self.metrics.copy()

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
