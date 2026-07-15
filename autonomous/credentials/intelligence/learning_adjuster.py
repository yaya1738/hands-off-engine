class LearningAdjuster:

    def adjust(
        self,
        diagnosis,
        base_confidence,
        history
    ):

        matches = [
            item for item in history
            if item.get("diagnosis") == diagnosis
        ]

        if not matches:
            return {
                "diagnosis": diagnosis,
                "confidence": base_confidence,
                "source": "base",
                "mode": "read_only",
            }

        resolved = [
            item for item in matches
            if item.get("outcome") == "resolved"
        ]

        bonus = min(
            0.1,
            len(resolved) * 0.02
        )

        return {
            "diagnosis": diagnosis,
            "confidence":
                min(1.0, base_confidence + bonus),
            "historical_support":
                len(resolved),
            "source":
                "history_adjusted",
            "mode":
                "read_only",
        }
