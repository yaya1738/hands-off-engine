class IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningRetrieval:

    def query(self, query, records):

        matches = [
            record
            for record in records
            if record.get(
                "learning_event"
            ) == query
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
                )
                if matches
                else 0,
            "mode":
                "read_only",
        }
