from typing import Any, Dict, List


class FactorySelfAssessment:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def assess(
        self,
        metrics: Dict[str, Any],
    ):
        success_rate = metrics.get(
            "success_rate",
            0,
        )

        health = success_rate

        result = {
            "health": health,
            "gaps": self.detect_gaps(
                metrics
            ),
            "objective": metrics.get(
                "objective"
            ),
            "context": metrics.get(
                "context",
                "",
            ),
            "target": metrics.get(
                "target",
                "",
            ),
            "development_type": metrics.get(
                "development_type",
                "",
            ),
            "capability_context": metrics.get(
                "capability_context",
                {},
            ),
        }

        self._history.append(
            result
        )

        return result

    def detect_gaps(
        self,
        metrics: Dict[str, Any],
    ):
        gaps = []

        if metrics.get(
            "success_rate",
            0,
        ) < 0.8:
            gaps.append(
                "low success rate"
            )

        if metrics.get(
            "average_impact",
            0,
        ) < 0.3:
            gaps.append(
                "low improvement impact"
            )

        return gaps

    def recommend(
        self,
        assessment: Dict[str, Any],
    ):
        recommendations = []

        for gap in assessment.get(
            "gaps",
            [],
        ):
            recommendations.append(
                f"improve {gap}"
            )

        return recommendations

    def history(self):
        return self._history
