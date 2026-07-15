class ConfidenceCalibrator:

    def calibrate(
        self,
        confidence,
        sample_size,
        contradiction_count=0
    ):

        if sample_size <= 0:
            adjusted = confidence * 0.5

        else:
            sample_factor = min(
                1.0,
                sample_size / 100
            )

            adjusted = (
                confidence * 0.7
                +
                sample_factor * 0.3
            )

        penalty = min(
            0.5,
            contradiction_count * 0.1
        )

        adjusted = max(
            0.0,
            adjusted - penalty
        )

        return {
            "calibrated_confidence": round(
                adjusted,
                3
            ),
            "sample_size": sample_size,
            "contradictions": contradiction_count,
            "mode": "read_only",
        }
