class IntelligenceImprovementPatternMemory:

    def analyze(self, events):

        recommendations = [
            event.get("recommendation")
            for event in events
        ]

        if recommendations:

            return {
                "pattern":
                    "confidence_tracking_recurrence",
                "occurrences":
                    len(recommendations),
                "confidence":
                    events[-1].get(
                        "confidence",
                        0
                    ),
                "mode":
                    "read_only",
            }

        return {
            "pattern": None,
            "occurrences": 0,
            "confidence": 0,
            "mode": "read_only",
        }
