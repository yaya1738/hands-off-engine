from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryDevelopmentTracker:
    def __init__(self):
        self._tasks: List[Dict[str, Any]] = []
        self._next_id = 1

    def create_task(
        self,
        task: Dict[str, Any],
    ):
        record = {
            "id": self._next_id,
            "task": task,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._next_id += 1

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

    def verify_task(
        self,
        task_id: int,
        verification: Dict[str, Any],
    ):
        for task in self._tasks:
            if task["id"] == task_id:
                task["verification"] = verification
                task["status"] = "verified"
                task["verified_at"] = (
                    datetime.now(timezone.utc).isoformat()
                )

                return task

        return None

    def history(self):
        return self._tasks
