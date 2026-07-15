from typing import Any, Dict, List


class FactoryRuntimeDashboard:
    def __init__(
        self,
        health=None,
        audit=None,
    ):
        self.health_source = health
        self.audit_source = audit
        self._history: List[Dict[str, Any]] = []

    def health(self):
        if self.health_source:
            return self.health_source()

        return {
            "status": "UNKNOWN",
        }

    def history(self):
        if self.audit_source:
            return self.audit_source()

        return []

    def snapshot(self):
        result = {
            "health": self.health(),
            "events": self.history(),
        }

        self._history.append(
            result
        )

        return result

    def summary(self):
        snapshot = self.snapshot()

        result = {
            "health_status": snapshot["health"].get(
                "status"
            ),
            "event_count": len(
                snapshot["events"]
            ),
        }

        self._history.append(
            result
        )

        return result

    def records(self):
        return self._history
