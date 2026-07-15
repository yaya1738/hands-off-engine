from typing import Any, Dict, List


class FactoryScheduler:
    def __init__(self):
        self._jobs: List[Dict[str, Any]] = []

    def schedule(
        self,
        job_id: str,
        action: str,
        interval: int,
    ) -> None:
        self._jobs.append(
            {
                "job_id": job_id,
                "action": action,
                "interval": interval,
                "status": "SCHEDULED",
                "runs": 0,
            }
        )

    def run_pending(self):
        results = []

        for job in self._jobs:
            job["runs"] += 1
            job["status"] = "RUNNING"

            results.append(
                {
                    "job_id": job["job_id"],
                    "action": job["action"],
                }
            )

            job["status"] = "COMPLETE"

        return results

    def list_jobs(self):
        return self._jobs
