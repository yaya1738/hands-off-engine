from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryAlertManager:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def classify(
        self,
        issue: str,
    ):
        if issue in (
            "critical",
            "failure",
            "down",
        ):
            return "CRITICAL"

        if issue in (
            "degraded",
            "warning",
        ):
            return "WARNING"

        return "INFO"

    def create_alert(
        self,
        issue: str,
    ):
        alert = {
            "issue": issue,
            "level": self.classify(
                issue
            ),
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._history.append(
            alert
        )

        return alert

    def history(self):
        return self._history
