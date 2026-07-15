from typing import Dict, List, Any


class ProvisioningAuditIndex:
    def __init__(self):
        self._records: List[Any] = []

    def add(self, record: Any) -> None:
        self._records.append(record)

    def get_by_request_id(self, request_id: str) -> List[Any]:
        return [
            record
            for record in self._records
            if record.request_id == request_id
        ]

    def get_by_decision(self, decision: str) -> List[Any]:
        return [
            record
            for record in self._records
            if record.decision == decision
        ]

    def get_by_policy_version(self, version: str) -> List[Any]:
        return [
            record
            for record in self._records
            if record.policy_version == version
        ]
