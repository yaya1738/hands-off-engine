from ai.factory.development_executor import FactoryDevelopmentExecutor

from typing import Any, Dict, List


class FactoryDevelopmentOrchestrator:
    def __init__(self):
        self.tasks: List[Dict[str, Any]] = []
        self.executor = FactoryDevelopmentExecutor()
        self._history: List[Dict[str, Any]] = []

    def create_development_task(
        self,
        task: Dict[str, Any],
    ):
        entry = {
            "status": "created",
            "task": task,
            "validation": [],
        }

        self.tasks.append(entry)
        self._history.append(entry)

        return entry

    def update_status(
        self,
        task_id: Any,
        status: str,
    ):
        for task in self.tasks:
            if task.get("task", {}).get("id") == task_id:
                task["status"] = status
                self._history.append(task)
                return task

        result = {
            "updated": False,
            "task_id": task_id,
        }

        self._history.append(result)

        return result

    def record_validation(
        self,
        task_id: Any,
        validation: Dict[str, Any],
    ):
        for task in self.tasks:
            if task.get("task", {}).get("id") == task_id:
                task["validation"].append(validation)
                self._history.append(task)
                return task

        result = {
            "recorded": False,
            "task_id": task_id,
        }

        self._history.append(result)

        return result

    def execute_task(
        self,
        task: Dict[str, Any],
    ):
        result = self.executor.execute(
            task
        )

        self._history.append(
            result
        )

        return result

    def report(self):
        return {
            "tasks": self.tasks,
            "count": len(self.tasks),
        }

    def history(self):
        return self._history
