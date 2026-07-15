class CredentialOutcomeMemory:

    def __init__(self):
        self.records = []


    def record(self, diagnosis, investigation, outcome):

        self.records.append(
            {
                "diagnosis": diagnosis,
                "investigation": investigation,
                "outcome": outcome,
            }
        )


    def summarize(self):

        summary = {}

        for record in self.records:

            key = record["diagnosis"]

            if key not in summary:
                summary[key] = {
                    "count": 0,
                    "successful_outcomes": 0
                }

            summary[key]["count"] += 1

            if record["outcome"] == "confirmed":
                summary[key]["successful_outcomes"] += 1

        return summary
