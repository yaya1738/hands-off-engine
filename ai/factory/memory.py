from typing import Any, List, Dict


class FactoryMemory:
    def __init__(self):
        self._records: List[Dict[str, Any]] = []

    def remember(self, record: Dict[str, Any]) -> None:
        self._records.append(record)

    def recall_all(self) -> List[Dict[str, Any]]:
        return self._records

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        return [
            record
            for record in self._records
            if record.get("status") == status
        ]
