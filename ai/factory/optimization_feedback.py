from typing import Any, Dict, List


class FactoryOptimizationFeedback:
    def __init__(
        self,
        metrics=None,
    ):
        self.metrics = metrics
        self._history: List[Dict[str, Any]] = []

    def analyze(self):
        if self.metrics:
            snapshot = self.metrics.snapshot()

        else:
            snapshot = {}

        result = {
            "metrics": snapshot,
            "analyzed": True,
        }

        self._history.append(
            result
        )

        return result

    def recommend(self):
        analysis = self.analyze()

        result = {
            "recommendation": "OPTIMIZE",
            "based_on": analysis,
        }

        self._history.append(
            result
        )

        return result

    def apply_feedback(self):
        result = {
            "status": "APPLIED",
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
