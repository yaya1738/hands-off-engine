class IntelligenceContextEnhancer:

    def enhance(
        self,
        signal,
        current_confidence,
        historical_confidence,
    ):

        delta = round(
            current_confidence - historical_confidence,
            2
        )

        if abs(delta) <= 0.1:
            quality = "consistent"
        elif delta < 0:
            quality = "confidence_decline"
        else:
            quality = "confidence_improvement"

        return {
            "signal": signal,
            "current_confidence": current_confidence,
            "historical_confidence": historical_confidence,
            "confidence_delta": delta,
            "context_quality": quality,
            "mode": "read_only",
        }
