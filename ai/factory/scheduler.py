from typing import Any, Dict, List


class FactoryScheduler:
    def __init__(self):
        self.tasks: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def schedule_task(
        self,
        task: Dict[str, Any],
    ):
        self.tasks.append(
            task
        )

        result = {
            "scheduled": True,
            "task": task,
        }

        self._history.append(result)

        return result

    def cancel_task(
        self,
        task: Dict[str, Any],
    ):
        result = {
            "cancelled": True,
            "task": task,
        }

        self._history.append(result)

        return result

    def run_due_tasks(self):
        result = {
            "executed": True,
            "count": len(self.tasks),
        }

        self._history.append(result)

        return result

    def check_schedule(self):
        result = {
            "checked": True,
            "count": len(self.tasks),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
