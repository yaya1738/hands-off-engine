from typing import Any, Dict


class FactoryStateManager:
    def __init__(self):
        self._state: Dict[str, Any] = {}

    def set(
        self,
        key: str,
        value: Any,
    ):
        self._state[key] = value

    def get(
        self,
        key: str,
        default=None,
    ):
        return self._state.get(
            key,
            default,
        )

    def update(
        self,
        values: Dict[str, Any],
    ):
        self._state.update(
            values
        )

    def snapshot(self):
        return dict(
            self._state
        )
