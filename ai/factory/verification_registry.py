from typing import Any, Dict, List


class FactoryVerificationRegistry:
    def __init__(self):
        self._verifications: List[Dict[str, Any]] = []

    def record_verification(
        self,
        verification_id: str,
        artifact_id: str,
        status: str,
        details: Dict[str, Any] = None,
    ) -> None:
        self._verifications.append(
            {
                "verification_id": verification_id,
                "artifact_id": artifact_id,
                "status": status,
                "details": details or {},
            }
        )

    def get_verification(
        self,
        verification_id: str,
    ):
        for item in self._verifications:
            if item["verification_id"] == verification_id:
                return item

        return None

    def find_by_artifact(
        self,
        artifact_id: str,
    ):
        return [
            item
            for item in self._verifications
            if item["artifact_id"] == artifact_id
        ]

    def list_verifications(self):
        return self._verifications
