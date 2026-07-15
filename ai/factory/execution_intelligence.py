from typing import Any, Dict, List


class FactoryExecutionIntelligence:
    def __init__(self):
        self.executions: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def create_execution(
        self,
        execution_id: str,
        execution: Dict[str, Any],
    ):
        execution = dict(execution)
        execution["status"] = "created"
        self.executions[execution_id] = execution

        result = {
            "created": True,
            "execution_id": execution_id,
        }

        self._history.append(result)
        return result

    def start_execution(
        self,
        execution_id: str,
    ):
        if execution_id in self.executions:
            self.executions[execution_id]["status"] = "running"

        result = {
            "started": True,
            "execution_id": execution_id,
        }

        self._history.append(result)
        return result

    def track_execution(
        self,
        execution_id: str,
    ):
        result = {
            "tracked": True,
            "execution": self.executions.get(execution_id),
        }

        self._history.append(result)
        return result

    def complete_execution(
        self,
        execution_id: str,
    ):
        if execution_id in self.executions:
            self.executions[execution_id]["status"] = "completed"

        result = {
            "completed": True,
            "execution_id": execution_id,
        }

        self._history.append(result)
        return result

    def history(self):
        return self._history
