class IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningConsolidator:

    def consolidate(self, feedback):

        return {
            "learning_event":
                "forecast_feedback_consolidated",
            "reliability":
                feedback.get(
                    "accuracy",
                    0
                ),
            "memory_updated":
                True,
            "mode":
                "read_only",
        }
