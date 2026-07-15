from typing import Any, Callable, Dict, List


class FactoryRuntimeScheduler:
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
            "status": "SCHEDULED",
        }

        self._jobs.append(
            job
        )

        return job

    def run(self):
        results = []

        for job in self._jobs:
            if job["status"] == "SCHEDULED":
                result = job["task"]()

                entry = {
                    "name": job["name"],
                    "result": result,
                }

                job["status"] = "COMPLETE"

                self._history.append(
                    entry
                )

                results.append(
                    entry
                )

        return results

    def cancel(
        self,
        name: str,
    ):
        for job in self._jobs:
            if job["name"] == name:
                job["status"] = "CANCELLED"
                return job

        return None

    def history(self):
        return self._history
