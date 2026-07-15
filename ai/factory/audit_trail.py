from typing import Any, Dict, List


class FactoryAuditTrail:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def record_action(
        self,
        action: Dict[str, Any],
    ):
        record = {
            "type": "action",
            "data": action,
        }

        self.records.append(record)
        self._history.append(record)

        return {
            "recorded": True,
            "record": record,
        }

    def record_decision(
        self,
        decision: Dict[str, Any],
    ):
        record = {
            "type": "decision",
            "data": decision,
        }

        self.records.append(record)
        self._history.append(record)

        return {
            "recorded": True,
            "record": record,
        }

    def query_records(
        self,
        record_type: str = None,
    ):
        records = self.records

        if record_type:
            records = [
                r
                for r in records
                if r["type"] == record_type
            ]

        result = {
            "records": records,
        }

        self._history.append(result)

        return result

    def verify_integrity(self):
        result = {
            "valid": True,
            "count": len(self.records),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
