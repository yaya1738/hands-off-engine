from typing import Any, Dict, List


class FactoryPerformanceEvaluation:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def evaluate_action(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "evaluated": True,
            "action": action,
        }

        self.results.append(
            result
        )

        self._history.append(
            result
        )

        return result

    def measure_impact(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ):
        result = {
            "impact_measured": True,
            "before": before,
            "after": after,
        }

        self._history.append(
            result
        )

        return result

    def compare_results(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any],
    ):
        result = {
            "matched": expected == actual,
        }

        self._history.append(
            result
        )

        return result

    def score_performance(
        self,
        result: Dict[str, Any],
    ):
        score = {
            "score": 1,
        }

        self._history.append(
            score
        )

        return score

    def history(self):
        return self._history
