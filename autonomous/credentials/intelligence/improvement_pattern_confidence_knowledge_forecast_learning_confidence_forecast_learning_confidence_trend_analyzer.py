class IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningConfidenceTrendAnalyzer:

    def analyze(self, history):

        item = (
            history[0]
            if history
            else {}
        )

        return {
            "trend":
                "stable",
            "knowledge":
                item.get(
                    "knowledge"
                ),
            "confidence":
                item.get(
                    "confidence",
                    0
                ),
            "mode":
                "read_only",
        }
