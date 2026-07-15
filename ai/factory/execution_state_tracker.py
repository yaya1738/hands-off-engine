from typing import Any, Dict, List


class FactoryExecutionStateTracker:
    def __init__(self):
        self.executions: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_execution(
        self,
        action: Dict[str, Any],
    ):
        execution = {
            "action": action,
            "status": "PLANNED",
        }

        self.executions.append(
            execution
        )

        self._history.append(
            execution
        )

        return execution

    def update_status(
        self,
        execution: Dict[str, Any],
        status: str,
    ):
        execution["status"] = status

        result = {
            "updated": True,
            "status": status,
        }

        self._history.append(
            result
        )

        return result

    def get_state(
        self,
        execution: Dict[str, Any],
    ):
        result = {
            "status": execution.get(
                "status"
            ),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
