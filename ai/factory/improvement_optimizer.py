from typing import Any, Dict, List


class FactoryImprovementOptimizer:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def score(
        self,
        improvement: Dict[str, Any],
    ):
        impact = improvement.get(
            "impact",
            0,
        )

        success = improvement.get(
            "success_rate",
            0,
        )

        risk = improvement.get(
            "risk",
            0,
        )

        score = (
            (impact * 0.5)
            + (success * 0.5)
            - (risk * 0.25)
        )

        result = {
            "improvement": improvement,
            "score": score,
        }

        self._history.append(
            result
        )

        return result

    def rank(
        self,
        improvements: List[Dict[str, Any]],
    ):
        return sorted(
            [
                self.score(
                    improvement
                )
                for improvement in improvements
            ],
            key=lambda item: item["score"],
            reverse=True,
        )

    def select(
        self,
        improvements,
    ):
        ranked = self.rank(
            improvements
        )

        if not ranked:
            return None

        return ranked[0]

    def history(self):
        return self._history
