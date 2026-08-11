from typing import Any, Dict, List


class FactoryCapabilityPerformance:

    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def record(
        self,
        capability: str,
        outcome: Dict[str, Any],
    ):
        entry = {
            "capability": capability,
            "outcome": outcome,
        }

        self._history.append(entry)

        return entry

    def success_rate(
        self,
        capability: str,
    ):
        records = [
            item
            for item in self._history
            if item["capability"] == capability
        ]

        if not records:
            return 0

        successes = sum(
            1
            for item in records
            if item["outcome"].get("status")
            in (
                "EXECUTED",
                "COMPLETED",
            )
        )

        return successes / len(records)

    def history(self):
        return self._history
