class IntelligenceConfidenceCalibrator:

    def calibrate(self, records):

        total = len(records)

        if total == 0:
            return {
                "forecast_accuracy": 0,
                "calibration": "no_data",
                "observations": 0,
                "mode": "read_only",
            }

        correct = 0

        for item in records:
            if item["forecast"] == item["observed"]:
                correct += 1

        accuracy = round(
            correct / total,
            2
        )

        if accuracy >= 0.8:
            status = "good"
        elif accuracy >= 0.5:
            status = "moderate"
        else:
            status = "poor"

        return {
            "forecast_accuracy": accuracy,
            "calibration": status,
            "observations": total,
            "mode": "read_only",
        }
