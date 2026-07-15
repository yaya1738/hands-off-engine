class IntelligenceImprovementForecastEngine:

    def forecast(self, trend):

        if trend.get("trend") in (
            "stable",
            "increasing",
        ):
            return {
                "forecast": "continued_confidence_tracking_need",
                "confidence": 0.80,
                "basis": [
                    "improvement_history",
                    "trend_signal",
                ],
                "mode": "read_only",
            }

        return {
            "forecast": "no_clear_improvement_signal",
            "confidence": 0.40,
            "basis": [
                "weak_trend",
            ],
            "mode": "read_only",
        }
