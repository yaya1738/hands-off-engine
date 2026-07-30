from typing import Any, Callable, Dict, List


class FactoryWorkflowOrchestrator:
    def __init__(self):
        self._steps: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []

    def register_step(
        self,
        name: str,
        handler: Callable,
    ):
        self._steps[name] = handler

        result = {
            "registered": True,
            "step": name,
        }

        self._history.append(result)

        return result

    def execute_workflow(
        self,
        workflow: List[str],
        context: Dict[str, Any] | None = None,
    ):
        context = context or {}

        results = []

        for step in workflow:
            handler = self._steps.get(step)

            if not handler:
                result = {
                    "step": step,
                    "status": "NO_HANDLER",
                }
            else:
                try:
                    output = handler(context)

                    result = {
                        "step": step,
                        "status": "COMPLETED",
                        "output": output,
                    }

                except Exception as exc:
                    result = {
                        "step": step,
                        "status": "FAILED",
                        "error": str(exc),
                    }

            results.append(result)

        record = {
            "workflow": workflow,
            "results": results,
        }

        self._history.append(record)

        return record

    def steps(self):
        return list(self._steps.keys())

    def history(self):
        return self._history
