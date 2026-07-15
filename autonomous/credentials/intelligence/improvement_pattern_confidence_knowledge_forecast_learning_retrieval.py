class IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningRetrieval:

    def query(self, query, records):

        matches = [
            item
            for item in records
            if item.get("learning_event") == query
        ]

        reliability = (
            matches[0].get("reliability", 0)
            if matches
            else 0
        )

        return {
            "query":
                query,
            "matches":
                len(matches),
            "reliability":
                reliability,
            "mode":
                "read_only",
        }
