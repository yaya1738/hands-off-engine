class IntelligenceLearningConsolidator:

    def consolidate(self, resolution):

        accuracy = 1.0 if resolution.get("accuracy") else 0.0

        return {
            "learning_event": (
                "forecast_confirmed"
                if resolution.get("accuracy")
                else "forecast_failed"
            ),
            "accuracy": accuracy,
            "confidence": resolution.get(
                "confidence_update",
                0,
            ),
            "memory_updated": True,
            "mode": "read_only",
        }
