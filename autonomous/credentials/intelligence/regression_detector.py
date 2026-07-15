class RegressionDetector:

    def analyze(self, history):

        if len(history) < 2:
            return {
                "regression_detected": False,
                "reason": "insufficient_data",
                "mode": "read_only",
            }

        previous = history[-2].get(
            "confidence",
            0
        )

        current = history[-1].get(
            "confidence",
            0
        )

        drop = previous - current

        if drop >= 0.10:
            return {
                "regression_detected": True,
                "reason": "confidence_drop",
                "previous_confidence": previous,
                "current_confidence": current,
                "mode": "read_only",
            }

        return {
            "regression_detected": False,
            "reason": "stable",
            "previous_confidence": previous,
            "current_confidence": current,
            "mode": "read_only",
        }
