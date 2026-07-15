class IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningSummarizer:

    def summarize(self, ranking):

        top = (
            ranking[0]
            if ranking
            else {}
        )

        return {
            "summary":
                top.get(
                    "knowledge"
                ),
            "confidence":
                top.get(
                    "score",
                    0
                ),
            "mode":
                "read_only",
        }
