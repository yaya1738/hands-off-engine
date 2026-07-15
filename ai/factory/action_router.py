from typing import Any, Callable, Dict, List


class FactoryActionRouter:
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []

    def register_handler(
        self,
        action: str,
        handler: Callable,
    ):
        self._handlers[action] = handler

    def route(
        self,
        decision: Dict[str, Any],
    ):
        action = decision.get(
            "decision",
            "UNKNOWN",
        )

        handler = self._handlers.get(
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
                    "status": "ROUTED",
                    "output": output,
                }

            except Exception as exc:
                result = {
                    "action": action,
                    "status": "FAILED",
                    "error": str(exc),
                }

        self._history.append(result)

        return result

    def history(self):
        return self._history
