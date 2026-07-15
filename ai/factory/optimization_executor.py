from datetime import datetime, timezone
from typing import Any, Callable, Dict, List


class FactoryOptimizationExecutor:
    def __init__(self):
        self._actions: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []

    def register_action(
        self,
        action: str,
        handler: Callable,
    ):
        self._actions[action] = handler

    def execute(
        self,
        optimization: Dict[str, Any],
    ):
        action = optimization.get(
            "action",
            "UNKNOWN",
        )

        handler = self._actions.get(
            action
        )

        if not handler:
            result = {
                "action": action,
                "status": "NO_HANDLER",
            }

        else:
            try:
                output = handler()

                result = {
                    "action": action,
                    "status": "COMPLETED",
                    "output": output,
                }

            except Exception as exc:
                result = {
                    "action": action,
                    "status": "FAILED",
                    "error": str(exc),
                }

        result["timestamp"] = datetime.now(
            timezone.utc
        ).isoformat()

        self._history.append(result)

        return result

    def history(self):
        return self._history
