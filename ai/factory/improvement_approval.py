from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryImprovementApproval:
    def __init__(self):
        self._requests: List[Dict[str, Any]] = []
        self._next_request_id = 1

    def request(
        self,
        improvement: Dict[str, Any],
    ):
        request = {
            "approval_id": (
                f"improvement-approval-{self._next_request_id}"
            ),
            "improvement": improvement,
            "status": "PENDING",
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._next_request_id += 1
        self._requests.append(request)

        return request

    def _is_registered_request(
        self,
        request: Dict[str, Any],
    ):
        return any(
            registered is request
            or (
                registered.get("approval_id")
                and registered.get("approval_id")
                == request.get("approval_id")
            )
            for registered in self._requests
        )

    def approve(
        self,
        request: Dict[str, Any],
    ):
        if not isinstance(request, dict):
            return {
                "status": "BLOCKED",
                "reason": "invalid_approval_request",
            }

        if not self._is_registered_request(request):
            return {
                "status": "BLOCKED",
                "reason": "unregistered_approval_request",
            }

        if request.get("status") != "PENDING":
            return {
                "status": "BLOCKED",
                "reason": "approval_request_not_pending",
                "approval_id": request.get("approval_id"),
            }

        request["status"] = "APPROVED"

        improvement = request.get(
            "improvement"
        )

        if improvement:
            improvement["status"] = "APPROVED"

        return request

    def validate_approved_request(
        self,
        request: Dict[str, Any],
    ):
        if not isinstance(request, dict):
            return {
                "status": "BLOCKED",
                "reason": "invalid_approval_request",
            }

        if not self._is_registered_request(request):
            return {
                "status": "BLOCKED",
                "reason": "unregistered_approval_request",
            }

        if request.get("status") != "APPROVED":
            return {
                "status": "BLOCKED",
                "reason": "approval_request_not_approved",
                "approval_id": request.get("approval_id"),
            }

        improvement = request.get("improvement")

        if not isinstance(improvement, dict):
            return {
                "status": "BLOCKED",
                "reason": "approval_request_missing_improvement",
                "approval_id": request.get("approval_id"),
            }

        return {
            "status": "APPROVED",
            "approval_id": request.get("approval_id"),
            "improvement": improvement,
        }

    def reject(
        self,
        request: Dict[str, Any],
    ):
        if not isinstance(request, dict):
            return {
                "status": "BLOCKED",
                "reason": "invalid_approval_request",
            }

        if not self._is_registered_request(request):
            return {
                "status": "BLOCKED",
                "reason": "unregistered_approval_request",
            }

        if request.get("status") != "PENDING":
            return {
                "status": "BLOCKED",
                "reason": "approval_request_not_pending",
                "approval_id": request.get("approval_id"),
            }

        request["status"] = "REJECTED"

        return request

    def history(self):
        return self._requests
