from typing import Any, Dict, List


class FactoryExperimentLearning:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def analyze(
        self,
        experiments: List[Dict[str, Any]],
    ):
        total = len(experiments)

        promoted = len(
            [
                exp
                for exp in experiments
                if exp.get("decision")
                == "PROMOTE"
            ]
        )

        rejected = total - promoted

        result = {
            "total": total,
            "promoted": promoted,
            "rejected": rejected,
            "success_rate": (
                promoted / total
                if total
                else 0
            ),
        }

        self._history.append(
            result
        )

        return result

    def success_rate(
        self,
        experiments,
    ):
        return self.analyze(
            experiments
        )["success_rate"]

    def recommend(
        self,
        experiments,
    ):
        rate = self.success_rate(
            experiments
        )

        if rate >= 0.8:
            return "allow_more_tests"

        if rate >= 0.5:
            return "continue_testing"

        return "tighten_policy"

    def history(self):
        return self._history
