from datetime import datetime, timezone


class IntelligenceAuditTrail:

    def __init__(self):
        self.records = []

    def record(self, summary):

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": summary["decision"],
            "risk": summary["risk"],
            "confidence": summary["confidence"],
            "mode": "read_only",
        }

        self.records.append(entry)

        return entry

    def history(self):
        return self.records
