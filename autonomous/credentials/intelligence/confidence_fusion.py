class ConfidenceFusion:

    def calculate(
        self,
        base_confidence,
        history_support,
        pattern_reliability,
    ):

        score = (
            base_confidence * 0.5
            + history_support * 0.25
            + pattern_reliability * 0.25
        )

        return {
            "confidence": round(score, 3),
            "components": {
                "base": base_confidence,
                "history": history_support,
                "pattern": pattern_reliability,
            },
            "mode": "read_only",
        }
