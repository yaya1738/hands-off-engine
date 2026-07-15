class IntelligenceImprovementPatternLearningConsolidator:

    def consolidate(self, feedback):

        return {
            "learning_event":
                "pattern_feedback_consolidated",
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
