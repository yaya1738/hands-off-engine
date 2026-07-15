from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryJobResults:
    def __init__(self):
        self._results: List[Dict[str, Any]] = []

    def record(
        self,
        job_id: str,
        status: str,
        output: Any = None,
    ) -> None:
        self._results.append(
            {
                "job_id": job_id,
                "status": status,
                "output": output,
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
            }
        )

    def get(
        self,
        job_id: str,
    ):
        for result in self._results:
            if result["job_id"] == job_id:
                return result

        return None

    def list(self):
        return self._results

    def find_by_status(
        self,
        status: str,
    ):
        return [
            result
            for result in self._results
            if result["status"] == status
        ]
