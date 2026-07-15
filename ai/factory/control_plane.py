from typing import Any, Dict


class FactoryControlPlane:
    def __init__(
        self,
        runtime: Any,
        snapshot_store: Any,
        snapshot_diff: Any,
        optimizer: Any,
    ):
        self.runtime = runtime
        self.snapshot_store = snapshot_store
        self.snapshot_diff = snapshot_diff
        self.optimizer = optimizer

    def inspect(self) -> Dict[str, Any]:
        return {
            "health": self.runtime.status(),
            "dashboard": self.runtime.view(),
        }

    def save_state(
        self,
        snapshot: Dict[str, Any],
    ):
        self.snapshot_store.save_snapshot(
            snapshot
        )

    def latest_state(self):
        return self.snapshot_store.get_latest()

    def compare_states(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ):
        return self.snapshot_diff.compare(
            before,
            after,
        )

    def optimize(self):
        return self.optimizer.optimize()
