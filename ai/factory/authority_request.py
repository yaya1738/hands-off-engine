from typing import Any, Dict


class FactoryAuthorityRequest:
    """Build a bounded authority request from an already-derived Factory plan.

    This adapter does not authorize, persist, route, or execute work. It only
    converts planner output into the explicit identity fields required by the
    governed authority boundary.
    """

    @staticmethod
    def build(plan: Dict[str, Any], *, msg_id: str = "", task_id: str = "") -> Dict[str, Any]:
        if not isinstance(plan, dict):
            return {"available": False}

        objective = plan.get("goal") or plan.get("objective")
        if not objective or not isinstance(objective, str):
            return {"available": False}

        correlation = {
            "msg_id": str(msg_id) if msg_id else None,
            "task_id": str(task_id) if task_id else None,
        }
        return {
            "available": True,
            "command": {
                "id": correlation["msg_id"] or correlation["task_id"] or "",
                "mode": "DRYRUN",
                "approval_status": "pending",
                "objective": objective,
                "priority": plan.get("priority", 0),
                "correlation": correlation,
            },
        }


__all__ = ["FactoryAuthorityRequest"]
