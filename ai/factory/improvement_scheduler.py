from datetime import datetime, timezone
from typing import Any, Callable, Dict, List


class FactoryImprovementScheduler:
    def __init__(self):
        self._jobs: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def schedule(
        self,
        name: str,
        task: Callable,
    ):
        job = {
            "name": name,
            "task": task,
        }

        self._jobs.append(
            job
        )

        return job

    def run_cycle(self):
        results = []

        for job in self._jobs:
            result = job["task"]()

            entry = {
                "name": job["name"],
                "result": result,
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            self._history.append(
                entry
            )

            results.append(
                entry
            )

        return results

    def history(self):
        return self._history
