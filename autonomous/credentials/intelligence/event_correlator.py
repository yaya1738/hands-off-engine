from collections import Counter


class IntelligenceEventCorrelator:

    def analyze(self, events):

        if not events:
            return {
                "correlation": "no_events",
                "mode": "read_only",
            }

        types = [
            e.get("event_type")
            for e in events
        ]

        counts = Counter(types)

        repeated = [
            key
            for key, value in counts.items()
            if value > 1
        ]

        if repeated:
            return {
                "correlation":
                    "repeated_intelligence_signal",
                "events_detected":
                    len(events),
                "repeated_events":
                    repeated,
                "severity":
                    "medium",
                "mode":
                    "read_only",
            }

        return {
            "correlation":
                "single_signal",
            "events_detected":
                len(events),
            "severity":
                "low",
            "mode":
                "read_only",
        }
