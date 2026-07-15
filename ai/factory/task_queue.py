from typing import Any, Dict, List


class FactoryTaskQueue:
    def __init__(self):
        self._tasks: List[Dict[str, Any]] = []

    def add_task(
        self,
        task_id: str,
        goal: str,
    ) -> None:
        self._tasks.append(
            {
                "task_id": task_id,
                "goal": goal,
                "status": "QUEUED",
            }
        )

    def next_task(self):
        for task in self._tasks:
            if task["status"] == "QUEUED":
                task["status"] = "RUNNING"
                return task

        return None

    def complete_task(
        self,
        task_id: str,
        result: Any,
    ) -> None:
        for task in self._tasks:
            if task["task_id"] == task_id:
                task["status"] = "COMPLETE"
                task["result"] = result

    def list_tasks(self):
        return self._tasks
