class IntelligenceImprovementPatternMemorySummarizer:

    def summarize(self, ranking):

        top = ranking[0] if ranking else {}

        return {
            "summary":
                top.get(
                    "pattern"
                ),
            "confidence":
                top.get(
                    "score",
                    0
                ),
            "mode":
                "read_only",
        }
