class IntelligenceImprovementMemoryConsolidator:

    def consolidate(self, memories, feedback):

        confirmed = sum(
            1 for item in feedback
            if item.get("feedback")
            == "improvement_confirmed"
        )

        total = len(feedback)

        reliability = (
            confirmed / total
            if total
            else 0
        )

        knowledge = (
            memories[0].get("improvement_id")
            if memories
            else None
        )

        return {
            "knowledge": knowledge,
            "confirmed_events": confirmed,
            "reliability": reliability,
            "mode": "read_only",
        }
