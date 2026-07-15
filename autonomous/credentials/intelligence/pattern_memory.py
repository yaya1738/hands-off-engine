from datetime import datetime, timezone


class IntelligencePatternMemory:

    def __init__(self):
        self.memory = []

    def store(self, pattern):

        now = datetime.now(timezone.utc).isoformat()

        entry = {
            "pattern_id": pattern["pattern"],
            "occurrences": pattern["occurrences"],
            "confidence": pattern["confidence"],
            "first_seen": now,
            "last_seen": now,
            "mode": "read_only",
        }

        self.memory.append(entry)

        return entry

    def recall(self):
        return self.memory
