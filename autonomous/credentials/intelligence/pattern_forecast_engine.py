class IntelligencePatternForecastEngine:

    def forecast(self, trend):

        if (
            trend.get("trend") == "increasing"
            and trend.get("confidence", 0) >= 0.8
        ):
            result = "continued_high_risk_pattern"
            confidence = 0.82
            basis = [
                "increasing_trend",
                "persistent_pattern",
            ]

        else:
            result = "pattern_stabilization_possible"
            confidence = 0.6
            basis = [
                "limited_signal",
            ]

        return {
            "forecast": result,
            "pattern": trend.get("pattern"),
            "confidence": confidence,
            "basis": basis,
            "mode": "read_only",
        }
