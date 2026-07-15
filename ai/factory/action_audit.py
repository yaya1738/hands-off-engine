from typing import Any, Dict, List


class FactoryActionAudit:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def record_action(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "type": "ACTION",
            "data": action,
        }

        self.records.append(
            result
        )

        self._history.append(
            result
        )

        return result

    def record_decision(
        self,
        decision: Dict[str, Any],
    ):
        result = {
            "type": "DECISION",
            "data": decision,
        }

        self.records.append(
            result
        )

        self._history.append(
            result
        )

        return result

    def record_outcome(
        self,
        outcome: Dict[str, Any],
    ):
        result = {
            "type": "OUTCOME",
            "data": outcome,
        }

        self.records.append(
            result
        )

        self._history.append(
            result
        )

        return result

    def query(
        self,
        record_type: str = None,
    ):
        if record_type:
            result = [
                item
                for item in self.records
                if item["type"] == record_type
            ]

        else:
            result = self.records

        self._history.append(
            {
                "query": record_type,
                "results": result,
            }
        )

        return result

    def history(self):
        return self._history
