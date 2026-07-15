class IntelligenceImprovementPatternConfidenceTracker:

    def track(self, summary_history):

        latest = summary_history[-1] if summary_history else {}

        return {
            "pattern":
                latest.get(
                    "summary"
                ),
            "confidence":
                latest.get(
                    "confidence",
                    0
                ),
            "history_entries":
                len(summary_history),
            "mode":
                "read_only",
        }
