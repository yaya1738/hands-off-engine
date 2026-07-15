from collections import Counter


class CredentialCorrelationEngine:

    def analyze(self, events):

        diagnoses = Counter()

        for event in events:
            diagnoses[
                event.get("diagnosis")
            ] += 1

        patterns = []

        for diagnosis, count in diagnoses.items():

            if count >= 3:

                patterns.append(
                    {
                        "pattern":
                        diagnosis,

                        "occurrences":
                        count,

                        "signal":
                        "correlated_event_cluster",

                        "mode":
                        "read_only",
                    }
                )

        return patterns
