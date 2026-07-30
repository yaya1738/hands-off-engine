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


    def schedule(
        self,
        job_id,
        action,
        delay,
    ):
        if not hasattr(self, "_jobs"):
            self._jobs = []

        job = {
            "id": job_id,
            "action": action,
            "delay": delay,
            "status": "SCHEDULED",
            "runs": 0,
        }

        self._jobs.append(job)

        return job


    def run_pending(self):
        jobs = getattr(
            self,
            "_jobs",
            [],
        )

        for job in jobs:
            job["runs"] = job.get(
                "runs",
                0,
            ) + 1
            job["status"] = "COMPLETE"

        return jobs


    def list_jobs(self):
        return getattr(
            self,
            "_jobs",
            [],
        )
