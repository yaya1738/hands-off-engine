class IntelligenceDecisionSummary:

    def summarize(
        self,
        response,
        risk,
        confidence,
        historical_confidence,
        priority,
    ):

        return {
            "decision": response,
            "risk": risk,
            "confidence": confidence,
            "historical_confidence": historical_confidence,
            "priority": priority,
            "mode": "read_only",
        }
