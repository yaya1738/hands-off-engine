class IntelligenceImprovementPatternConfidenceTrendAnalyzer:

    def analyze(self, history):

        latest = history[-1] if history else {}

        return {
            "trend":
                "stable",
            "pattern":
                latest.get(
                    "pattern"
                ),
            "confidence":
                latest.get(
                    "confidence",
                    0
                ),
            "mode":
                "read_only",
        }
