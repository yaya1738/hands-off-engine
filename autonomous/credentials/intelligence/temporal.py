from datetime import datetime


class CredentialTemporalAnalyzer:

    def parse_time(self, value):

        if not value:
            return None

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except Exception:
            return None


    def analyze(self, events):

        timestamps = []

        for event in events:

            ts = self.parse_time(
                event.get("timestamp")
            )

            if ts:
                timestamps.append(ts)

        timestamps.sort()

        if len(timestamps) < 2:
            return {
                "event_count": len(events),
                "time_analysis": "insufficient_data"
            }

        duration = (
            timestamps[-1] -
            timestamps[0]
        ).total_seconds()

        return {
            "event_count": len(events),
            "observed_window_seconds": duration,
            "first_event": timestamps[0].isoformat(),
            "last_event": timestamps[-1].isoformat(),
        }
