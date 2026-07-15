from typing import Any, Dict, List


class FactorySnapshotPublisher:
    def __init__(
        self,
        observability: Any,
        state_stream: Any,
    ):
        self.observability = observability
        self.state_stream = state_stream
        self._history: List[Dict[str, Any]] = []

    def publish(
        self,
        job_results=None,
    ):
        snapshot = self.observability.snapshot(
            job_results
        )

        self.state_stream.publish_state(
            snapshot
        )

        self._history.append(snapshot)

        return snapshot

    def publish_now(self):
        return self.publish()

    def history(self):
        return self._history
