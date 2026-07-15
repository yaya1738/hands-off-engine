from typing import Any, Dict, List


class FactoryOptimizationLoop:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def analyze(
        self,
        metrics: Dict[str, Any],
    ):
        success_rate = metrics.get(
            "success_rate",
            0,
        )

        if success_rate >= 0.9:
            return {
                "status": "OPTIMAL",
                "action": "CONTINUE",
            }

        if success_rate >= 0.5:
            return {
                "status": "DEGRADED",
                "action": "IMPROVE",
            }

        return {
            "status": "CRITICAL",
            "action": "RESTRUCTURE",
        }

    def optimize(
        self,
        metrics: Dict[str, Any],
    ):
        result = self.analyze(
            metrics
        )

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
