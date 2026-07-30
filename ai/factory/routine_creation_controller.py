from typing import Any, Dict, List

from ai.factory.routine_creation_pipeline import (
    FactoryRoutineCreationPipeline,
)


class FactoryRoutineCreationController:
    def __init__(self):
        self.pipeline = FactoryRoutineCreationPipeline()
        self._queue: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def submit_requirement(
        self,
        requirement: Dict[str, Any],
    ):
        self._queue.append(requirement)

        return {
            "submitted": True,
            "queue_size": len(self._queue),
        }

    def process_queue(self):
        results = []

        while self._queue:
            requirement = self._queue.pop(0)

            result = self.pipeline.create_from_requirement(
                requirement.get("description", ""),
                requirement["name"],
                requirement["purpose"],
                requirement["steps"],
                requirement.get("dependencies", []),
            )

            results.append(result)
            self._history.append(result)

        return {
            "processed": len(results),
            "results": results,
        }

    def status(self):
        return {
            "queued": len(self._queue),
            "completed": len(self._history),
        }

    def history(self):
        return self._history
