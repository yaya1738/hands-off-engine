class IntelligenceForecastCalibrator:

    def calibrate(self, forecast_history):

        total = len(forecast_history)

        if total == 0:
            accuracy = 0
            quality = "unknown"

        else:
            correct = sum(
                1 for item in forecast_history
                if item.get("forecast")
                == item.get("observed")
            )

            accuracy = round(correct / total, 2)

            if accuracy >= 0.75:
                quality = "good"
            elif accuracy >= 0.5:
                quality = "moderate"
            else:
                quality = "poor"

        return {
            "forecast_accuracy": accuracy,
            "calibration": quality,
            "observations": total,
            "mode": "read_only",
        }
