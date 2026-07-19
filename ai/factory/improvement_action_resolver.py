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
            return None

        return self._actions.get(name)
