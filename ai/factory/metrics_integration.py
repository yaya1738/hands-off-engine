from typing import Any, Dict, List


class FactoryMetricsIntegration:
    def __init__(
        self,
        metrics=None,
    ):
        self.metrics = metrics
        self._history: List[Dict[str, Any]] = []

    def on_cycle(self):
        if self.metrics:
            result = self.metrics.increment(
                "cycles"
            )

        else:
            result = {
                "status": "NO_METRICS",
            }

        self._history.append(
            result
        )

        return result

    def on_success(self):
        if self.metrics:
            result = self.metrics.increment(
                "successes"
            )

        else:
            result = {
                "status": "NO_METRICS",
            }

        self._history.append(
            result
        )

        return result

    def on_failure(self):
        if self.metrics:
            result = self.metrics.increment(
                "failures"
            )

        else:
            result = {
                "status": "NO_METRICS",
            }

        self._history.append(
            result
        )

        return result

    def snapshot(self):
        if self.metrics:
            result = self.metrics.snapshot()

        else:
            result = {}

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
