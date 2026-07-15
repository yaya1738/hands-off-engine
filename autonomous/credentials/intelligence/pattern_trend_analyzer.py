class IntelligencePatternTrendAnalyzer:

    def analyze(self, history):

        if len(history) < 2:
            trend = "stable"

        elif history[-1]["occurrences"] > history[0]["occurrences"]:
            trend = "increasing"

        elif history[-1]["occurrences"] < history[0]["occurrences"]:
            trend = "reducing"

        else:
            trend = "stable"

        return {
            "pattern": history[-1]["pattern_id"],
            "trend": trend,
            "occurrences": history[-1]["occurrences"],
            "confidence": 0.86,
            "mode": "read_only",
        }


    def analyse(self, history):
        return self.analyze(history)
