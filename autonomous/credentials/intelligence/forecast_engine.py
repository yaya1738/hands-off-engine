class IntelligenceForecastEngine:

    def forecast(
        self,
        trend,
        health,
        confidence,
    ):

        evidence = []

        if trend == "declining":
            evidence.append(
                "confidence_decline"
            )

        if health == "degraded":
            evidence.append(
                "health_degraded"
            )

        if confidence < 0.7:
            evidence.append(
                "low_confidence"
            )

        if len(evidence) >= 2:
            result = "continued_degradation_risk"
            score = 0.76

        else:
            result = "stable_outlook"
            score = 0.8

        return {
            "forecast":
                result,

            "confidence":
                score,

            "basis":
                evidence,

            "mode":
                "read_only",
        }
