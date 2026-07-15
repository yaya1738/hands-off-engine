class IntelligenceImprovementPatternMemoryQuery:

    def query(self, search_term, records):

        matches = [
            record
            for record in records
            if record.get("recommendation") == search_term
        ]

        return {
            "query":
                search_term,
            "matches":
                len(matches),
            "reliability":
                1.0 if matches else 0,
            "mode":
                "read_only",
        }
