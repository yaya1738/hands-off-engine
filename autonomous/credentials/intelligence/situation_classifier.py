class SituationClassifier:

    def classify(self, correlation):

        if correlation.get("correlation") == (
            "repeated_intelligence_signal"
        ):
            return {
                "situation":
                    "attention_required",
                "cause":
                    correlation.get("correlation"),
                "severity":
                    correlation.get("severity"),
                "confidence":
                    0.8,
                "mode":
                    "read_only",
            }

        return {
            "situation":
                "normal_operation",
            "cause":
                "no_pattern",
            "severity":
                "low",
            "confidence":
                0.9,
            "mode":
                "read_only",
        }
