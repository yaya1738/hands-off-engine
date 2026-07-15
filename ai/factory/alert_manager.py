from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryAlertManager:
    def __init__(self):
        self._active: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def raise_alert(
        self,
        alert_type: str,
        component: str,
        details=None,
    ):
        alert = {
            "type": alert_type,
            "component": component,
            "details": details,
            "status": "ACTIVE",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._active.append(alert)
        self._history.append(alert)

        return alert

    def resolve_alert(
        self,
        component: str,
    ):
        resolved = []

        for alert in self._active:
            if alert["component"] == component:
                alert["status"] = "RESOLVED"
                resolved.append(alert)

        self._active = [
            alert
            for alert in self._active
            if alert["component"] != component
        ]

        return resolved

    def active_alerts(self):
        return self._active

    def history(self):
        return self._history
