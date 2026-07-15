class IntelligenceTrendAnalyzer:

    def analyse(self, snapshots):
        return self.analyze(snapshots)

    def analyze(self, snapshots):

        if len(snapshots) < 2:
            return {
                "trend": "insufficient_data",
                "observations": len(snapshots),
                "mode": "read_only",
            }

        first = snapshots[0]
        last = snapshots[-1]

        if last.get("confidence", 0) < first.get("confidence", 0):
            trend = "declining"

        elif last.get("confidence", 0) > first.get("confidence", 0):
            trend = "improving"

        else:
            trend = "stable"

        return {
            "trend":
                trend,

            "observations":
                len(snapshots),

            "confidence_direction":
                trend,

            "mode":
                "read_only",
        }
