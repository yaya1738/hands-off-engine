from typing import Any, List


class ProvisioningAuditQuery:
    def __init__(self):
        self._records: List[Any] = []

    def add(self, record: Any) -> None:
        self._records.append(record)

    def find_by_request_id(self, request_id: str) -> List[Any]:
        return [
            record
            for record in self._records
            if getattr(record, "request_id", None) == request_id
        ]

    def find_by_decision(self, decision: str) -> List[Any]:
        return [
            record
            for record in self._records
            if getattr(record, "decision", None) == decision
        ]

    def find_by_policy_version(self, version: str) -> List[Any]:
        return [
            record
            for record in self._records
            if getattr(record, "policy_version", None) == version
        ]
