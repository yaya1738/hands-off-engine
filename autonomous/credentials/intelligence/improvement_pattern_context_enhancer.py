class IntelligenceImprovementPatternContextEnhancer:

    def enhance(self, signal, knowledge):

        return {
            "signal":
                signal,
            "historical_match":
                knowledge.get("query"),
            "reliability":
                knowledge.get(
                    "reliability",
                    0
                ),
            "context_quality":
                "enhanced",
            "mode":
                "read_only",
        }
