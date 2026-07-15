from ai.factory.snapshot_publisher import (
    FactorySnapshotPublisher,
)


class FakeObservability:
    def snapshot(self, results=None):
        return {
            "health": "HEALTHY",
        }


class FakeStateStream:
    def __init__(self):
        self.state = None

    def publish_state(self, state):
        self.state = state


def test_publish():
    stream = FakeStateStream()

    publisher = FactorySnapshotPublisher(
        FakeObservability(),
        stream,
    )

    result = publisher.publish()

    assert result["health"] == "HEALTHY"
    assert stream.state["health"] == "HEALTHY"


def test_history():
    publisher = FactorySnapshotPublisher(
        FakeObservability(),
        FakeStateStream(),
    )

    publisher.publish()

    assert len(publisher.history()) == 1


def test_publish_now():
    publisher = FactorySnapshotPublisher(
        FakeObservability(),
        FakeStateStream(),
    )

    result = publisher.publish_now()

    assert result["health"] == "HEALTHY"
