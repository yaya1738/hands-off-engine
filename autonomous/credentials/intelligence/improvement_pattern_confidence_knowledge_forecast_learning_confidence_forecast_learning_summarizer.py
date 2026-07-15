class IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningSummarizer:

    def summarize(self, ranking):

        item = (
            ranking[0]
            if ranking
            else {}
        )

        return {
            "summary":
                item.get(
                    "knowledge"
                ),
            "confidence":
                item.get(
                    "score",
                    0
                ),
            "mode":
                "read_only",
        }
