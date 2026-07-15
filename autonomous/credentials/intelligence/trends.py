from collections import Counter


class CredentialTrendAnalyzer:

    def analyze(self, events):

        transitions = Counter()
        reasons = Counter()

        for event in events:

            transition = (
                f"{event.get('from')}"
                f"->{event.get('to')}"
            )

            transitions[transition] += 1

            if event.get("reason"):
                reasons[event["reason"]] += 1

        return {
            "transition_counts": dict(transitions),
            "reason_counts": dict(reasons),
            "event_volume": len(events),
        }
