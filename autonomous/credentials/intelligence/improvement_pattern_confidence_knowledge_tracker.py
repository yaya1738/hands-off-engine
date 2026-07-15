class IntelligenceImprovementPatternConfidenceKnowledgeTracker:

    def track(self, summaries):

        latest = summaries[0] if summaries else {}

        return {
            "knowledge":
                latest.get(
                    "summary"
                ),
            "confidence":
                latest.get(
                    "confidence",
                    0
                ),
            "history_entries":
                len(summaries),
            "mode":
                "read_only",
        }
