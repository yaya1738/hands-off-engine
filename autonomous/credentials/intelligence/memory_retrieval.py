class IntelligenceMemoryRetrieval:

    def retrieve(self, memories, query):

        matches = [
            item for item in memories
            if item.get("signal") == query
        ]

        confidence_values = [
            item["confidence"]
            for item in matches
        ]

        confidence = (
            round(
                sum(confidence_values) / len(confidence_values),
                2
            )
            if confidence_values
            else 0
        )

        return {
            "query": query,
            "matches": len(matches),
            "historical_confidence": confidence,
            "mode": "read_only",
        }
