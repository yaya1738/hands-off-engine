class IntelligenceImprovementTrendAnalyzer:

    def analyze(self, records):

        if not records:
            return {
                "trend": "unknown",
                "top_improvement": None,
                "occurrences": 0,
                "mode": "read_only",
            }

        top = max(
            records,
            key=lambda x: x.get("occurrences", 0)
        )

        return {
            "trend": (
                "increasing"
                if top.get("occurrences", 0) > 1
                else "stable"
            ),
            "top_improvement": top.get(
                "improvement_id"
            ),
            "occurrences": top.get(
                "occurrences",
                0
            ),
            "mode": "read_only",
        }
