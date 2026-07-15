from typing import Any, Dict


class OptimizationFeedback:
    def build_feedback(
        self,
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        success_rate = metrics.get(
            "success_rate",
            0,
        )

        if success_rate >= 0.9:
            trend = "healthy"
            recommendation = "continue"

        elif success_rate >= 0.5:
            trend = "unstable"
            recommendation = "review"

        else:
            trend = "poor"
            recommendation = "improve"

        return {
            "performance": success_rate,
            "trend": trend,
            "recommendation": recommendation,
        }

    def score_performance(
        self,
        metrics: Dict[str, Any],
    ):
        return metrics.get(
            "success_rate",
            0,
        )

    def recommend(
        self,
        metrics: Dict[str, Any],
    ):
        return self.build_feedback(
            metrics
        )["recommendation"]
