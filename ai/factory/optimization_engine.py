from typing import Any, Dict, List


class FactoryOptimizationEngine:
    def __init__(self):
        self.optimizations: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def evaluate_options(
        self,
        options: List[Dict[str, Any]],
    ):
        result = {
            "evaluated": True,
            "count": len(options),
        }

        self._history.append(result)

        return result

    def rank_improvements(
        self,
        improvements: List[Dict[str, Any]],
    ):
        result = {
            "ranked": True,
            "count": len(improvements),
        }

        self._history.append(result)

        return result

    def apply_optimization(
        self,
        optimization: Dict[str, Any],
    ):
        self.optimizations.append(
            optimization
        )

        result = {
            "applied": True,
            "optimization": optimization,
        }

        self._history.append(result)

        return result

    def measure_gain(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ):
        result = {
            "measured": True,
            "before": before,
            "after": after,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
