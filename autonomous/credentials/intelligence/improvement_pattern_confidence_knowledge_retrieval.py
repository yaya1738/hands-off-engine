class IntelligenceImprovementPatternConfidenceKnowledgeRetrieval:

    def query(self, term, records):

        matches = [
            record
            for record in records
            if term in str(record)
        ]

        return {
            "query":
                term,
            "matches":
                len(matches),
            "reliability":
                1.0 if matches else 0,
            "mode":
                "read_only",
        }
