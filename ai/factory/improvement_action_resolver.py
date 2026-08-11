from typing import Any, Callable, Dict, Optional


class FactoryImprovementActionResolver:
    def __init__(self):
        self._actions: Dict[str, Callable] = {}

    def register_action(
        self,
        name: str,
        handler: Callable,
    ):
        self._actions[name] = handler

    def resolve(
        self,
        action: Dict[str, Any],
    ) -> Optional[Callable]:
        name = action.get("action")

        if not name:
            if action.get("failure_fingerprint"):
                return self._actions.get("failure_repair")
            return None

        resolved = self._actions.get(name)

        if resolved:
            return resolved

        if action.get("failure_fingerprint"):
            return self._actions.get("failure_repair")

        return None
