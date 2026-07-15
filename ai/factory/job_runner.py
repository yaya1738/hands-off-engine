from typing import Any, Dict, List


class FactoryJobRunner:
    def __init__(
        self,
        executor: Any,
    ):
        self.executor = executor
        self._history: List[Dict[str, Any]] = []

    def run_job(
        self,
        job_type: str,
        payload: Any = None,
    ):
        result = self.executor.execute(
            job_type,
            payload,
        )

        record = {
            "job_type": job_type,
            "result": result,
        }

        self._history.append(record)

        return record

    def run_cycle(
        self,
        jobs: List[Dict[str, Any]],
    ):
        results = []

        for job in jobs:
            results.append(
                self.run_job(
                    job["action"],
                    job.get("payload"),
                )
            )

        return results

    def history(self):
        return self._history
