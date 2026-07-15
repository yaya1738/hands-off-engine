from typing import Any, Dict, List


class FactorySelfOptimizer:
    def __init__(
        self,
    ):
        self.parameters: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []

    def evaluate(
        self,
        metrics: Dict[str, Any],
    ):
        score = metrics.get(
            "success_rate",
            0,
        )

        result = {
            "performance": score,
            "status": (
                "GOOD"
                if score >= 0.8
                else "NEEDS_OPTIMIZATION"
            ),
        }

        self._history.append(
            result
        )

        return result

    def tune(
        self,
        parameter: str,
        value: Any,
    ):
        self.parameters[parameter] = value

        result = {
            "parameter": parameter,
            "value": value,
        }

        self._history.append(
            result
        )

        return result

    def optimize(
        self,
        metrics: Dict[str, Any],
    ):
        evaluation = self.evaluate(
            metrics
        )

        if evaluation["status"] == "NEEDS_OPTIMIZATION":
            action = self.tune(
                "optimization_mode",
                "ACTIVE",
            )

        else:
            action = {
                "action": "MAINTAIN",
            }

        result = {
            "evaluation": evaluation,
            "action": action,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
