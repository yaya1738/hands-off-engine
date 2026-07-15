from typing import Any, Dict, List


class FactoryImprovementQueue:
    def __init__(self):
        self._pending: List[Dict[str, Any]] = []
        self._running: List[Dict[str, Any]] = []
        self._completed: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def enqueue(
        self,
        improvement: Dict[str, Any],
    ):
        improvement.setdefault(
            "status",
            "PENDING",
        )

        self._pending.append(
            improvement
        )

        self._history.append(
            {
                "action": "ENQUEUE",
                "improvement": improvement,
            }
        )

        return improvement

    def dequeue(self):
        if not self._pending:
            return None

        improvement = self._pending.pop(
            0
        )

        improvement["status"] = "RUNNING"

        self._running.append(
            improvement
        )

        return improvement

    def complete(
        self,
        improvement: Dict[str, Any],
        result: Dict[str, Any],
    ):
        improvement["status"] = "COMPLETE"
        improvement["result"] = result

        if improvement in self._running:
            self._running.remove(
                improvement
            )

        self._completed.append(
            improvement
        )

        self._history.append(
            {
                "action": "COMPLETE",
                "improvement": improvement,
            }
        )

        return improvement

    def pending(self):
        return self._pending

    def history(self):
        return self._history
