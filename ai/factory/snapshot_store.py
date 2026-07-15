from typing import Any, Dict, List


class FactorySnapshotStore:
    def __init__(self):
        self._snapshots: List[Dict[str, Any]] = []

    def save_snapshot(
        self,
        snapshot: Dict[str, Any],
    ) -> None:
        self._snapshots.append(snapshot)

    def get_latest(self):
        if not self._snapshots:
            return None

        return self._snapshots[-1]

    def list_snapshots(self):
        return self._snapshots
