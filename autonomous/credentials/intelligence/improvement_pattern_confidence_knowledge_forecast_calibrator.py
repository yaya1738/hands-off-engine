class IntelligenceImprovementPatternConfidenceKnowledgeForecastCalibrator:

    def calibrate(self, observations):

        correct = [
            item
            for item in observations
            if item.get("forecast") == item.get("outcome")
        ]

        accuracy = (
            len(correct) / len(observations)
            if observations
            else 0
        )

        return {
            "forecast_accuracy":
                accuracy,
            "calibration":
                "good" if accuracy >= 0.8 else "needs_review",
            "observations":
                len(observations),
            "mode":
                "read_only",
        }
