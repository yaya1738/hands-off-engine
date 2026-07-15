class IntelligenceResponsePlanner:

    def plan(
        self,
        risk_level,
        risk_score,
        factors,
    ):

        if risk_level == "high":
            response = "human_review_priority"
            priority = 90

        elif risk_level == "medium":
            response = "monitor_closely"
            priority = 60

        else:
            response = "continue_observation"
            priority = 30

        return {
            "response": response,
            "priority": priority,
            "risk_score": risk_score,
            "reason": factors,
            "mode": "read_only",
        }
