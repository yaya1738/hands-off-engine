class IntelligenceImprovementPatternTrendAnalyzer:

    def analyze(self, pattern):

        occurrences = pattern.get(
            "occurrences",
            0
        )

        if occurrences > 1:
            trend = "increasing"
        else:
            trend = "stable"

        return {
            "pattern":
                pattern.get("pattern"),
            "trend":
                trend,
            "occurrences":
                occurrences,
            "confidence":
                pattern.get("confidence"),
            "mode":
                "read_only",
        }
