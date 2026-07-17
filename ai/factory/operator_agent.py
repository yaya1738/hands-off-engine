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

        result = {
            "integrity": integrity,
            "status": (
                "healthy"
                if integrity and integrity.get("healthy")
                else "attention_required"
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
