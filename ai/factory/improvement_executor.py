from datetime import datetime, timezone
from typing import Any, Callable, Dict, List


class FactoryImprovementExecutor:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def validate(
        self,
        improvement: Dict[str, Any],
    ):
        return (
            improvement.get(
                "status"
            )
            == "APPROVED"
        )

    def execute(
        self,
        improvement: Dict[str, Any],
        action: Callable,
    ):
        if not self.validate(
            improvement
        ):
            result = {
                "status": "BLOCKED",
                "reason": "not_approved",
            }

        else:
            try:
                output = action()

                result = {
                    "status": "EXECUTED",
                    "output": output,
                }

            except Exception as exc:
                result = {
                    "status": "FAILED",
                    "error": str(exc),
                }

        self.record(
            improvement,
            result,
        )

        return result

    def record(
        self,
        improvement: Dict[str, Any],
        result: Dict[str, Any],
    ):
        entry = {
            "improvement": improvement,
            "result": result,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._history.append(
            entry
        )

        return entry

    def history(self):
        return self._history
