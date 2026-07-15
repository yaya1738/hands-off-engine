class IntelligenceRiskScorer:

    def score(
        self,
        anomaly,
        health,
        trend,
        stability,
    ):

        risk = 0
        factors = []

        if anomaly:
            risk += 0.25
            factors.append("confidence_shift")

        if health == "degraded":
            risk += 0.25
            factors.append("health_degraded")

        if trend == "declining":
            risk += 0.25
            factors.append("trend_declining")

        if stability < 0.8:
            risk += 0.15
            factors.append("stability_reduction")

        if risk >= 0.7:
            level = "high"
        elif risk >= 0.4:
            level = "medium"
        else:
            level = "low"

        return {
            "risk_level": level,
            "risk_score": round(risk, 2),
            "factors": factors,
            "mode": "read_only",
        }
