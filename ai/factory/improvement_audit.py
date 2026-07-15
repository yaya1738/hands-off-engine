from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryImprovementAudit:
    def __init__(self):
        self._records: List[Dict[str, Any]] = []

    def record(
        self,
        action: Dict[str, Any],
    ):
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
