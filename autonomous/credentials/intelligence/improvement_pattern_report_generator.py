class IntelligenceImprovementPatternReportGenerator:

    def generate(self, decision):

        return {
            "system":
                "improvement_pattern_intelligence",
            "status":
                "stable",
            "recommendation":
                decision.get(
                    "recommendation"
                ),
            "confidence":
                decision.get(
                    "confidence"
                ),
            "priority":
                decision.get(
                    "priority"
                ),
            "mode":
                "read_only",
        }
