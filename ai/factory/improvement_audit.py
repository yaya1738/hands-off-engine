from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryImprovementAudit:

    def _json_safe(self, value):
        if isinstance(value, dict):
            return {
                k: self._json_safe(v)
                for k, v in value.items()
            }

        if isinstance(value, list):
            return [
                self._json_safe(v)
                for v in value
            ]

        if callable(value):
            return str(value)

        return value

    def __init__(self):
        self._records: List[Dict[str, Any]] = []

    def record(
        self,
        action: Dict[str, Any],
    ):
        action = self._json_safe(action)

        entry = {
            "action": action,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._records.append(
            entry
        )

        return entry

    def query(
        self,
        key: str,
        value: Any,
    ):
        return [
            record
            for record in self._records
            if record["action"].get(
                key
            )
            == value
        ]

    def history(self):
        return self._records
