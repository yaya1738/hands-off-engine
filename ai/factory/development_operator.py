from typing import Any, Dict, List


class FactoryDevelopmentOperator:
    def __init__(
        self,
        pipeline=None,
    ):
        self.pipeline = pipeline
        self.tasks: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def submit_task(
        self,
        task: Dict[str, Any],
    ):
        entry = {
            "task": task,
            "status": "submitted",
        }

        self.tasks.append(entry)
        self._history.append(entry)

        return entry

    def execute_cycle(
        self,
        task: Dict[str, Any],
    ):
        if self.pipeline:
            result = self.pipeline.run_development_cycle(
                task
            )
        else:
            result = {
                "status": "pipeline_unavailable",
                "task": task,
            }

        self._history.append(result)

        return result

    def review_status(self):
        return {
            "tasks": self.tasks,
            "count": len(self.tasks),
        }

    def history(self):
        return self._history
