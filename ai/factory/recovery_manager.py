from datetime import datetime, timezone
from typing import Any, Callable, Dict, List


class FactoryRecoveryManager:
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []

    def register_recovery(
        self,
        component: str,
        handler: Callable,
    ):
        self._handlers[component] = handler

    def recover(
        self,
        component: str,
    ):
        handler = self._handlers.get(
            component
        )

        if not handler:
            result = {
                "component": component,
                "status": "NO_HANDLER",
            }

        else:
            try:
                output = handler()

                result = {
                    "component": component,
                    "action": "RECOVER",
                    "status": "RECOVERED",
                    "output": output,
                }

            except Exception as exc:
                result = {
                    "component": component,
                    "action": "RECOVER",
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
