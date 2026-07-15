from typing import Any, Dict, List
import copy


class FactoryRuntimeState:
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self._snapshots: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def save_state(
        self,
        state: Dict[str, Any],
    ):
        self.state = copy.deepcopy(state)

        result = {
            "saved": True,
            "state": self.state,
        }

        self._history.append(result)

        return result

    def load_state(self):
        result = {
            "loaded": True,
            "state": copy.deepcopy(self.state),
        }

        self._history.append(result)

        return result

    def snapshot(self):
        snapshot = copy.deepcopy(self.state)

        self._snapshots.append(snapshot)

        result = {
            "snapshotted": True,
            "snapshot": snapshot,
        }

        self._history.append(result)

        return result

    def restore(
        self,
        snapshot: Dict[str, Any],
    ):
        self.state = copy.deepcopy(snapshot)

        result = {
            "restored": True,
            "state": self.state,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
