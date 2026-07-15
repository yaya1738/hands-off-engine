class IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningConfidenceTrendAnalyzer:

    def analyze(self, history):

        latest = (
            history[-1]
            if history
            else {}
        )

        return {
            "trend":
                "stable",
            "knowledge":
                latest.get(
                    "knowledge"
                ),
            "confidence":
                latest.get(
                    "confidence",
                    0
                ),
            "mode":
                "read_only",
        }
