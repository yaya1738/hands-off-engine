class IntelligenceImprovementConfidenceCalibrator:

    def calibrate(self, forecasts):

        observations = len(forecasts)

        if observations == 0:
            return {
                "forecast_accuracy": 0,
                "calibration": "unknown",
                "observations": 0,
                "mode": "read_only",
            }

        correct = sum(
            1 for item in forecasts
            if item.get("correct") is True
        )

        accuracy = correct / observations

        if accuracy >= 0.8:
            state = "good"
        elif accuracy >= 0.5:
            state = "moderate"
        else:
            state = "poor"

        return {
            "forecast_accuracy": accuracy,
            "calibration": state,
            "observations": observations,
            "mode": "read_only",
        }
