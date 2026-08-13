from typing import Any, Dict, List

from ai.factory.authority_gateway import FactoryAuthorityGateway


class FactoryAutonomousScheduler:
    """Schedule autonomous work while routing execution through Factory authority."""

    def __init__(self, authority=None):
        self.authority = authority or FactoryAuthorityGateway()
        self.tasks: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def schedule_task(self, task: Dict[str, Any]):
        self.tasks.append(task)
        result = {"scheduled": True, "task": task}
        self._history.append(result)
        return result

    def run_cycle(self):
        result = {"cycle_run": True, "task_count": len(self.tasks)}
        self._history.append(result)
        return result

    def run_self_improvement(self):
        return self.authority.execute_autonomous(
            "Run the Factory self-improvement cycle and apply only authorized improvements."
        )

    def prioritize_schedule(self):
        result = {
            "priority_task": self.tasks[0] if self.tasks else None,
        }
        self._history.append(result)
        return result

    def history(self):
        return self._history
