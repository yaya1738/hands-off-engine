class IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningRanking:

    def rank(self, records):

        ranking = []

        for item in records:
            ranking.append(
                {
                    "knowledge":
                        item.get(
                            "learning_event"
                        ),
                    "score":
                        item.get(
                            "reliability",
                            0
                        ),
                }
            )

        ranking.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return {
            "ranking":
                ranking,
            "mode":
                "read_only",
        }
