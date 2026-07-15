class IntelligenceImprovementPatternConfidenceKnowledgeSummarizer:

    def summarize(self, ranking):

        latest = ranking[0] if ranking else {}

        return {
            "summary":
                latest.get(
                    "knowledge"
                ),
            "confidence":
                latest.get(
                    "score",
                    0
                ),
            "mode":
                "read_only",
        }
