from typing import Any, Callable, Dict, List


class FactoryActionRouter:
    def __init__(self):
        self._actions: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []

    def register_action(
        self,
        action: str,
        handler: Callable,
    ) -> None:
        self._actions[action] = handler

    def route(
        self,
        decision: Dict[str, Any],
    ):
        action = decision.get(
            "decision",
            "REVIEW",
        )

        handler = self._actions.get(action)

        if not handler:
            result = {
                "error": "unknown_action",
                "action": action,
            }
        else:
            result = {
                "action": action,
                "result": handler(),
            }

        self._history.append(result)

        return result

    def available_actions(self):
        return list(self._actions.keys())

    def history(self):
        return self._history
