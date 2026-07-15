from collections import Counter


class ContextualPatternEngine:

    def analyze(self, events):

        patterns = []

        diagnosis_counts = Counter(
            event.get("diagnosis")
            for event in events
        )

        for diagnosis, count in diagnosis_counts.items():

            if count >= 2:

                providers = set(
                    event.get("provider")
                    for event in events
                    if event.get("diagnosis") == diagnosis
                )

                identities = set(
                    event.get("identity")
                    for event in events
                    if event.get("diagnosis") == diagnosis
                )

                patterns.append(
                    {
                        "diagnosis": diagnosis,
                        "occurrences": count,
                        "providers": list(providers),
                        "identity_count": len(identities),
                        "classification":
                        "contextual_cluster",
                        "mode":
                        "read_only",
                    }
                )

        return patterns
