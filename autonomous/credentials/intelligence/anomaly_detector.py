class IntelligenceAnomalyDetector:

    def detect(
        self,
        current_confidence,
        historical_confidence,
    ):

        deviation = round(
            current_confidence - historical_confidence,
            2
        )

        if abs(deviation) >= 0.1:
            anomaly = True
            anomaly_type = "confidence_shift"

            if abs(deviation) >= 0.2:
                severity = "high"
            else:
                severity = "medium"

        else:
            anomaly = False
            anomaly_type = None
            severity = "low"

        return {
            "anomaly_detected": anomaly,
            "type": anomaly_type,
            "severity": severity,
            "deviation": deviation,
            "mode": "read_only",
        }
