from datetime import datetime, timezone


class DecisionMemory:

    def __init__(self):
        self.records = []

    def record(
        self,
        diagnosis,
        recommendation,
        confidence,
        outcome
    ):

        entry = {
            "diagnosis": diagnosis,
            "recommendation": recommendation,
            "confidence": confidence,
            "outcome": outcome,
            "timestamp":
                datetime.now(timezone.utc)
                .isoformat(),
            "mode":
                "read_only",
        }

        self.records.append(entry)

        return entry

    def history(self):
        return self.records
