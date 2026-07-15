from typing import Any, Dict, List


class FactoryWorkflowEngine:
    def __init__(self):
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.executions: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_workflow(
        self,
        name: str,
        workflow: Dict[str, Any],
    ):
        self.workflows[name] = workflow

        result = {
            "created": True,
            "workflow": name,
        }

        self._history.append(result)

        return result

    def add_step(
        self,
        workflow_name: str,
        step: Dict[str, Any],
    ):
        workflow = self.workflows.setdefault(
            workflow_name,
            {"steps": []},
        )

        workflow.setdefault(
            "steps",
            []
        ).append(step)

        result = {
            "added": True,
            "workflow": workflow_name,
            "step": step,
        }

        self._history.append(result)

        return result

    def execute_workflow(
        self,
        workflow_name: str,
    ):
        result = {
            "executed": True,
            "workflow": workflow_name,
        }

        self.executions.append(result)
        self._history.append(result)

        return result

    def validate_workflow(
        self,
        workflow_name: str,
    ):
        result = {
            "validated": True,
            "workflow": workflow_name,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
