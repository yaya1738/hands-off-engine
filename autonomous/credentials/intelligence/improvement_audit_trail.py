from datetime import datetime, timezone


class IntelligenceImprovementAuditTrail:

    def __init__(self):
        self.events = []

    def record(self, report):

        event = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "event":
                "improvement_recommendation_generated",
            "recommendation":
                report.get("recommendation"),
            "confidence":
                report.get("confidence"),
            "mode":
                "read_only",
        }

        self.events.append(event)

        return event
