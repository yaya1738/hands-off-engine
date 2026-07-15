from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryResultCollector:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def collect(
        self,
        result: Dict[str, Any],
    ):
        record = {
            **result,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._history.append(
            record
        )

        return record

    def summarize(self):
        total = len(
            self._history
        )

        completed = len(
            [
                item
                for item in self._history
                if item.get("status")
                in (
                    "COMPLETED",
                    "ROUTED",
                    "RECOVERED",
                )
            ]
        )

        return {
            "total": total,
            "completed": completed,
            "success_rate": (
                completed / total
                if total
                else 0
            ),
        }

    def history(self):
        return self._history
