class AdaptiveConfidenceEngine:

    def adjust(
        self,
        diagnosis,
        base_confidence,
        history
    ):

        record = history.get(
            diagnosis,
            {}
        )

        total = record.get(
            "count",
            0
        )

        confirmed = record.get(
            "successful_outcomes",
            0
        )

        if total == 0:
            return {
                "diagnosis": diagnosis,
                "confidence": base_confidence,
                "source": "base_only",
                "mode": "read_only",
            }

        historical_rate = confirmed / total

        adjusted = (
            base_confidence * 0.5
            +
            historical_rate * 0.5
        )

        return {
            "diagnosis": diagnosis,
            "confidence": adjusted,
            "historical_support": historical_rate,
            "source": "history_adjusted",
            "mode": "read_only",
        }
