from datetime import datetime, timezone


class IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningConfidenceForecastFeedbackLoop:

    def record(self, calibration):

        return {
            "feedback":
                "forecast_calibration_recorded",
            "accuracy":
                calibration.get(
                    "forecast_accuracy",
                    0
                ),
            "learning_updated":
                True,
            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),
            "mode":
                "read_only",
        }
