from datetime import datetime, timezone


class IntelligenceForecastFeedbackLoop:

    def __init__(self):
        self.records = []

    def record(self, forecast):

        entry = {
            "feedback": "forecast_recorded",
            "forecast": forecast.get("forecast"),
            "outcome": "pending",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "memory_updated": True,
            "mode": "read_only",
        }

        self.records.append(entry)

        return entry

    def history(self):
        return self.records
