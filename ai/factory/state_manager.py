from typing import Any, Dict, List


class FactoryStateManager:
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []

    def save(
        self,
        state: Dict[str, Any],
    ):
        self.state = state.copy()

        result = {
            "status": "SAVED",
            "state": self.state,
        }

        self._history.append(
            result
        )

        return result

    def load(self):
        result = {
            "state": self.state,
        }

        self._history.append(
            result
        )

        return result

    def checkpoint(self):
        result = {
            "checkpoint": self.state.copy(),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
