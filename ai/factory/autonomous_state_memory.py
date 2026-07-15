from typing import Any, Dict, List


class FactoryAutonomousStateMemory:
    def __init__(self):
        self.states: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []

    def store_state(
        self,
        key: str,
        value: Any,
    ):
        self.states[key] = value

        result = {
            "stored": True,
            "key": key,
        }

        self._history.append(
            result
        )

        return result

    def retrieve_state(
        self,
        key: str,
    ):
        result = {
            "value": self.states.get(
                key
            ),
        }

        self._history.append(
            result
        )

        return result

    def update_state(
        self,
        key: str,
        value: Any,
    ):
        self.states[key] = value

        result = {
            "updated": True,
            "key": key,
        }

        self._history.append(
            result
        )

        return result

    def query_history(self):
        return self._history
