class IntelligenceImprovementDecisionSupport:

    def decide(self, context):

        if context.get("context_quality") == "enhanced":

            return {
                "recommendation":
                    "prioritize_confidence_tracking",
                "priority": "medium",
                "confidence": 0.85,
                "basis": [
                    "historical_match",
                    "reliability",
                    "current_signal",
                ],
                "mode": "read_only",
            }

        return {
            "recommendation": "no_clear_action",
            "priority": "low",
            "confidence": 0.40,
            "basis": [
                "insufficient_context",
            ],
            "mode": "read_only",
        }
