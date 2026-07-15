class IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningConfidenceTracker:

    def track(self, summary):

        return {
            "knowledge":
                summary.get(
                    "summary"
                ),
            "confidence":
                summary.get(
                    "confidence",
                    0
                ),
            "history_entries":
                1,
            "mode":
                "read_only",
        }
