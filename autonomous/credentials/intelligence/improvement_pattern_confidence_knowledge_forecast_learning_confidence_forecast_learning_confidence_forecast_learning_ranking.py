class IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningConfidenceForecastLearningConfidenceForecastLearningRanking:

    def rank(self, records):

        ranking = []

        for record in records:
            ranking.append(
                {
                    "knowledge":
                        record.get(
                            "learning_event"
                        ),
                    "score":
                        record.get(
                            "reliability",
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
