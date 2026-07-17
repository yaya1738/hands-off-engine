from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryDevelopmentTracker:
    def __init__(self):
        self._tasks: List[Dict[str, Any]] = []

    def create_task(
        self,
        task: Dict[str, Any],
    ):
        record = {
            "task": task,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._tasks.append(record)

        return record

    def update_status(
        self,
        index: int,
        status: str,
    ):
        self._tasks[index]["status"] = status

        return self._tasks[index]

    def complete_task(
        self,
        index: int,
    ):
        self._tasks[index]["status"] = "completed"
        self._tasks[index]["completed_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

        return self._tasks[index]

    def history(self):
        return self._tasks
