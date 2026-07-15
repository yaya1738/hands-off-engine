from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryIncidentManager:
    def __init__(self):
        self._incidents: List[Dict[str, Any]] = []

    def create(
        self,
        name: str,
        severity: str = "UNKNOWN",
    ):
        incident = {
            "name": name,
            "severity": severity,
            "status": "OPEN",
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._incidents.append(
            incident
        )

        return incident

    def update(
        self,
        incident: Dict[str, Any],
        status: str,
        note=None,
    ):
        incident["status"] = status

        if note:
            incident["note"] = note

        return incident

    def close(
        self,
        incident: Dict[str, Any],
        lesson=None,
    ):
        incident["status"] = "CLOSED"

        if lesson:
            incident["lesson"] = lesson

        return incident

    def history(self):
        return self._incidents
