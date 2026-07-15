class IntelligenceHealthMonitor:

    def assess(
        self,
        stability,
        confidence_trend,
    ):

        score = stability.get(
            "stability_score",
            0
        )

        if score >= 0.9:
            health = "healthy"

        elif score >= 0.6:
            health = "degraded"

        else:
            health = "unstable"

        return {
            "health":
                health,

            "stability_score":
                score,

            "confidence_trend":
                confidence_trend,

            "mode":
                "read_only",
        }
