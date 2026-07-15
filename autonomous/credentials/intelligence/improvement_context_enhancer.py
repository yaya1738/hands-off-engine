class IntelligenceImprovementContextEnhancer:

    def enhance(self, signal, knowledge):

        match = None
        reliability = 0

        for item in knowledge:
            if item.get("knowledge"):
                match = item.get("knowledge")
                reliability = item.get(
                    "reliability",
                    0
                )
                break

        return {
            "signal": signal,
            "historical_match": match,
            "reliability": reliability,
            "context_quality": "enhanced",
            "mode": "read_only",
        }
