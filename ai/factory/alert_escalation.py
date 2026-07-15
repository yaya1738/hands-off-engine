from typing import Any, Callable, Dict, List


class FactoryAlertEscalation:
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []

    def register_handler(
        self,
        action: str,
        handler: Callable,
    ):
        self._handlers[action] = handler

    def escalate(
        self,
        alert: Dict[str, Any],
    ):
        action = alert.get(
            "action",
            "ESCALATE",
        )

        handler = self._handlers.get(
            action
        )

        if not handler:
            result = {
                "action": action,
                "status": "NO_HANDLER",
                "alert": alert,
            }

        else:
            try:
                output = handler(alert)

                result = {
                    "action": action,
                    "status": "COMPLETED",
                    "output": output,
                    "alert": alert,
                }

            except Exception as exc:
                result = {
                    "action": action,
                    "status": "FAILED",
                    "error": str(exc),
                    "alert": alert,
                }

        self._history.append(result)

        return result

    def resolve(
        self,
        alert: Dict[str, Any],
    ):
        result = {
            "alert": alert,
            "status": "RESOLVED",
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
