from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryImprovementApproval:
    def __init__(self):
        self._requests: List[Dict[str, Any]] = []

    def request(
        self,
        improvement: Dict[str, Any],
    ):
        request = {
            "improvement": improvement,
            "status": "PENDING",
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._requests.append(
            request
        )

        return request

    def approve(
        self,
        request: Dict[str, Any],
    ):
        request["status"] = "APPROVED"

        return request

    def reject(
        self,
        request: Dict[str, Any],
    ):
        request["status"] = "REJECTED"

        return request

    def history(self):
        return self._requests
