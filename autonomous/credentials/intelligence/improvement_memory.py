class IntelligenceImprovementMemory:

    def __init__(self):
        self.records = {}

    def remember(self, improvement):

        key = improvement.get("improvement")

        if key not in self.records:
            self.records[key] = {
                "improvement_id": key,
                "occurrences": 0,
                "priority": improvement.get("priority"),
                "mode": "read_only",
            }

        self.records[key]["occurrences"] += 1

        return self.records[key]

    def all(self):
        return list(self.records.values())
