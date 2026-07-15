from datetime import datetime, timezone


class IntelligenceImprovementPatternAuditTrail:

    def record(self, report):

        return {
            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),
            "event":
                "improvement_pattern_recommendation_generated",
            "recommendation":
                report.get(
                    "recommendation"
                ),
            "confidence":
                report.get(
                    "confidence"
                ),
            "mode":
                "read_only",
        }
