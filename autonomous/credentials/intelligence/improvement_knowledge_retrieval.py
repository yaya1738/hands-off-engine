class IntelligenceImprovementKnowledgeRetrieval:

    def retrieve(self, knowledge, query):

        matches = [
            item for item in knowledge
            if item.get("knowledge") == query
        ]

        if matches:
            item = matches[0]

            return {
                "query": query,
                "matches": len(matches),
                "reliability": item.get(
                    "reliability",
                    0
                ),
                "mode": "read_only",
            }

        return {
            "query": query,
            "matches": 0,
            "reliability": 0,
            "mode": "read_only",
        }
