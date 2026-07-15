class IntelligenceImprovementPatternKnowledgeRetrieval:

    def retrieve(self, query, memory):

        matches = [
            item for item in memory
            if item.get("learning_event") == query
        ]

        return {
            "query":
                query,
            "matches":
                len(matches),
            "reliability":
                matches[0].get(
                    "reliability",
                    0
                ) if matches else 0,
            "mode":
                "read_only",
        }
