class IntelligenceImprovementPlanner:

    def plan(self, learning):

        if learning.get("accuracy", 0) >= 0.8:
            improvement = "increase_pattern_confidence_tracking"
            priority = "medium"
            basis = [
                "forecast_history",
                "learning_accuracy",
            ]

        else:
            improvement = "improve_forecast_reliability"
            priority = "high"
            basis = [
                "low_accuracy",
            ]

        return {
            "improvement": improvement,
            "priority": priority,
            "basis": basis,
            "mode": "read_only",
        }
