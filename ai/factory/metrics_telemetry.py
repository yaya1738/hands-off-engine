from typing import Any, Dict, List


class FactoryMetricsTelemetry:
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def record_metric(
        self,
        name: str,
        value: Any,
    ):
        self.metrics[name] = value

        result = {
            "recorded": True,
            "metric": name,
            "value": value,
        }

        self._history.append(
            result
        )

        return result

    def track_event(
        self,
        event: Dict[str, Any],
    ):
        self.events.append(
            event
        )

        result = {
            "tracked": True,
            "event": event,
        }

        self._history.append(
            result
        )

        return result

    def calculate_health(self):
        result = {
            "health": "GOOD",
            "metrics": len(
                self.metrics
            ),
            "events": len(
                self.events
            ),
        }

        self._history.append(
            result
        )

        return result

    def dashboard(self):
        result = {
            "metrics": self.metrics,
            "events": self.events,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
