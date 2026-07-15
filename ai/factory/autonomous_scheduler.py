from typing import Any, Dict, List


class FactoryAutonomousScheduler:
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

        self._history.append(
            result
        )

        return result

    def run_cycle(self):
        result = {
            "cycle_run": True,
            "task_count": len(
                self.tasks
            ),
        }

        self._history.append(
            result
        )

        return result

    def prioritize_schedule(self):
        result = {
            "priority_task": (
                self.tasks[0]
                if self.tasks
                else None
            ),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
