from ai.factory.daemon import FactoryDaemon


class FakeService:
    pass


class FakeOptimizer:
    def optimize(self):
        return {
            "action": "continue",
        }


class FakeStream:
    def __init__(self):
        self.state = None

    def publish_state(self, state):
        self.state = state


def test_start_stop():
    daemon = FactoryDaemon(
        FakeService()
    )

    assert daemon.start()["status"] == "started"
    assert daemon.status()["running"] is True

    assert daemon.stop()["status"] == "stopped"
    assert daemon.status()["running"] is False


def test_tick_runs_when_active():
    stream = FakeStream()

    daemon = FactoryDaemon(
        FakeService(),
        stream,
        FakeOptimizer(),
    )

    daemon.start()

    result = daemon.tick()

    assert result["status"] == "active"
    assert result["optimization"]["action"] == "continue"
    assert stream.state["status"] == "active"


def test_tick_inactive():
    daemon = FactoryDaemon(
        FakeService()
    )

    result = daemon.tick()

    assert result["status"] == "inactive"
