class IntelligenceSelfAssessment:

    def assess(
        self,
        stability,
        forecast_accuracy,
        trend,
    ):

        score = int(
            ((stability + forecast_accuracy) / 2) * 100
        ) / 100

        if score >= 0.8:
            quality = "healthy"
        elif score >= 0.6:
            quality = "acceptable"
        else:
            quality = "degraded"

        return {
            "intelligence_score": score,
            "quality": quality,
            "components": {
                "stability": stability,
                "forecast_accuracy": forecast_accuracy,
                "trend": trend,
            },
            "mode": "read_only",
        }
