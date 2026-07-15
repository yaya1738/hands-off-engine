class IntelligenceImprovementReportGenerator:

    def generate(self, decision):

        return {
            "system":
                "credential_bridge_improvement_intelligence",
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
