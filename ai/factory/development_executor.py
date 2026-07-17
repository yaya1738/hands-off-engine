from typing import Any, Dict, List


class FactoryDevelopmentExecutor:
    def __init__(self):
        self.executions: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def execute(
        self,
        task: Dict[str, Any],
    ):
        result = {
            "task": task,
            "status": "executed",
            "validation": "pending",
        }

        self.executions.append(result)
        self._history.append(result)

        return result

    def record_validation(
        self,
        execution_id: Any,
        validation: Dict[str, Any],
    ):
        for execution in self.executions:
            if execution.get("task", {}).get("id") == execution_id:
                execution["validation"] = validation

                self._history.append(execution)

                return execution

        result = {
            "updated": False,
            "execution_id": execution_id,
        }

        self._history.append(result)

        return result

    def report(self):
        return {
            "executions": self.executions,
            "count": len(self.executions),
        }

    def history(self):
        return self._history
