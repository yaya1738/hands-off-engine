from typing import Any, Dict, List


class FactoryOperatorAgent:
    def __init__(
        self,
        integrity_checker=None,
        goal_management=None,
        improvement_queue=None,
    ):
        self.integrity_checker = integrity_checker
        self.goal_management = goal_management
        self.improvement_queue = improvement_queue
        self._history: List[Dict[str, Any]] = []

    def assess(
        self,
        runtime,
    ):
        integrity = None

        if self.integrity_checker:
            integrity = self.integrity_checker.check_runtime(runtime)

        failed_components = []

        if integrity:
            failed_components = [
                name
                for name, healthy in integrity.get(
                    "checks",
                    {},
                ).items()
                if not healthy
            ]

        goal_count = 0
        if self.goal_management:
            goal_count = len(
                getattr(
                    self.goal_management,
                    "_history",
                    [],
                )
            )

        improvement_count = 0
        if self.improvement_queue:
            improvement_count = len(
                getattr(
                    self.improvement_queue,
                    "_history",
                    [],
                )
            )

        healthy = bool(
            integrity
            and integrity.get("healthy")
        )

        result = {
            "integrity": integrity,
            "status": (
                "healthy"
                if healthy
                else "attention_required"
            ),
            "failed_components": failed_components,
            "goal_count": goal_count,
            "improvement_queue_count": improvement_count,
            "reason": (
                "all factory contracts passing"
                if healthy
                else "factory components require inspection"
            ),
            "confidence": (
                1.0
                if healthy
                else 0.5
            ),
        }

        self._history.append(result)

        return result

    def choose_next_action(
        self,
        assessment: Dict[str, Any],
    ):
        if assessment.get("status") == "attention_required":
            action = "inspect_failed_components"
        else:
            action = "continue_improvement_cycle"

        result = {
            "action": action,
        }

        self._history.append(result)

        return result

    def report(self):
        return self._history
