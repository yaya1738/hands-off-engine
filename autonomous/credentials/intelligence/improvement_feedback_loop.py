from datetime import datetime, timezone


class IntelligenceImprovementFeedbackLoop:

    def record(self, forecast, outcome):

        confirmed = forecast == outcome

        return {
            "feedback": (
                "improvement_confirmed"
                if confirmed
                else "improvement_mismatch"
            ),
            "forecast": forecast,
            "outcome": outcome,
            "learning_updated": confirmed,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "mode": "read_only",
        }
