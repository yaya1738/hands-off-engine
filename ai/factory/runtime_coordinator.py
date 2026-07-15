from typing import Any, Dict


class FactoryRuntimeCoordinator:
    def __init__(
        self,
        lifecycle: Any,
        daemon_scheduler: Any,
        snapshot_publisher: Any = None,
    ):
        self.lifecycle = lifecycle
        self.daemon_scheduler = daemon_scheduler
        self.snapshot_publisher = snapshot_publisher

    def initialize(self) -> Dict[str, Any]:
        return self.lifecycle.startup()

    def run_cycle(self):
        result = self.daemon_scheduler.tick()

        if self.snapshot_publisher:
            snapshot = self.snapshot_publisher.publish()
            result["snapshot"] = snapshot

        return result

    def status(self):
        return self.daemon_scheduler.status()

    def shutdown(
        self,
        state: Dict[str, Any],
    ):
        return self.lifecycle.shutdown(
            state
        )
