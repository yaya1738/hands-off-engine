from typing import Any, Dict

from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.change_lifecycle_manager import FactoryChangeLifecycleManager


class FactoryDevelopmentPipeline:
    def __init__(self):
        self.orchestrator = FactoryDevelopmentOrchestrator()
        self.lifecycle = FactoryChangeLifecycleManager()
        self._history = []

    def run_development_cycle(
        self,
        task: Dict[str, Any],
    ):
        development_task = self.orchestrator.create_development_task(
            task
        )

        execution = self.orchestrator.execute_task(
            task
        )

        change = self.lifecycle.start_change(
            task
        )

        validation = self.lifecycle.validate_change(
            task
        )

        result = {
            "task": development_task,
            "execution": execution,
            "change": change,
            "validation": validation,
            "status": "ready_for_review",
        }

        self._history.append(result)

        return result

    def report(self):
        return {
            "cycles": len(self._history),
            "history": self._history,
        }
