class IntelligenceOutcomeResolver:

    def resolve(self, forecast_record, observed):

        predicted = forecast_record.get("forecast")

        accuracy = predicted == observed

        return {
            "forecast": predicted,
            "outcome": observed,
            "accuracy": accuracy,
            "confidence_update": 0.85 if accuracy else 0.45,
            "mode": "read_only",
        }
