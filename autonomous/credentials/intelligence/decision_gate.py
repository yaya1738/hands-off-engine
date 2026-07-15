class IntelligenceDecisionGate:

    def evaluate(
        self,
        intelligence_score,
        health,
        trend,
        calibration,
    ):

        reasons = []

        if health == "degraded":
            reasons.append("health_degraded")

        if trend == "declining":
            reasons.append("trend_declining")

        if calibration == "moderate":
            reasons.append("forecast_accuracy_moderate")

        if len(reasons) >= 2:
            status = "human_review_recommended"
            confidence = 0.78

        elif intelligence_score >= 0.8:
            status = "trusted"
            confidence = 0.85

        else:
            status = "observe_more"
            confidence = 0.70

        return {
            "gate_status": status,
            "confidence": confidence,
            "reasons": reasons,
            "mode": "read_only",
        }
