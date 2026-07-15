from typing import Any, Dict, List


class FactoryWorkflowIntelligence:
    def __init__(self):
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.steps: Dict[str, List[Dict[str, Any]]] = {}
        self._history: List[Dict[str, Any]] = []

    def create_workflow(
        self,
        name: str,
        workflow: Dict[str, Any],
    ):
        self.workflows[name] = workflow
        self.steps[name] = []

        result = {
            "created": True,
            "workflow": name,
        }

        self._history.append(result)

        return result

    def add_step(
        self,
        workflow: str,
        step: Dict[str, Any],
    ):
        self.steps.setdefault(
            workflow,
            []
        ).append(step)

        result = {
            "added": True,
            "workflow": workflow,
            "step": step,
        }

        self._history.append(result)

        return result

    def execute_workflow(
        self,
        workflow: str,
    ):
        result = {
            "executed": True,
            "workflow": workflow,
            "steps": len(
                self.steps.get(
                    workflow,
                    []
                )
            ),
        }

        self._history.append(result)

        return result

    def track_progress(
        self,
        workflow: str,
    ):
        result = {
            "tracked": True,
            "workflow": workflow,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
