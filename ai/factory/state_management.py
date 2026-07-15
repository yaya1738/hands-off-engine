from typing import Any, Dict, List


class FactoryStateManagement:
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.snapshots: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def set_state(
        self,
        key: str,
        value: Any,
    ):
        self.state[key] = value

        result = {
            "set": True,
            "key": key,
            "value": value,
        }

        self._history.append(
            result
        )

        return result

    def get_state(
        self,
        key: str,
    ):
        result = {
            "found": key in self.state,
            "value": self.state.get(key),
        }

        self._history.append(
            result
        )

        return result

    def update_state(
        self,
        updates: Dict[str, Any],
    ):
        self.state.update(
            updates
        )

        result = {
            "updated": True,
            "updates": updates,
        }

        self._history.append(
            result
        )

        return result

    def snapshot_state(self):
        snapshot = dict(
            self.state
        )

        self.snapshots.append(
            snapshot
        )

        result = {
            "snapshotted": True,
            "state": snapshot,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
