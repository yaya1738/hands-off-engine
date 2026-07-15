class IntelligenceImprovementPatternForecastCalibrator:

    def calibrate(self, forecast, outcome):

        accuracy = 1.0 if forecast == outcome else 0.0

        return {
            "forecast_accuracy": accuracy,
            "calibration":
                "good" if accuracy == 1.0 else "poor",
            "observations": 1,
            "mode": "read_only",
        }
