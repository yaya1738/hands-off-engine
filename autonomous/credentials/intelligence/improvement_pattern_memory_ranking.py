class IntelligenceImprovementPatternMemoryRanking:

    def rank(self, records):

        ranking = []

        for record in records:
            ranking.append(
                {
                    "pattern":
                        record.get(
                            "recommendation"
                        ),
                    "score":
                        record.get(
                            "confidence",
                            0
                        ),
                }
            )

        return {
            "ranking":
                ranking,
            "mode":
                "read_only",
        }
