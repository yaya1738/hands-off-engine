from ai.factory.lifecycle import (
    FactoryLifecycle,
)


class FakeDaemon:
    def __init__(self):
        self.running = False

    def start(self):
        self.running = True
        return {
            "status": "started",
        }

    def stop(self):
        self.running = False
        return {
            "status": "stopped",
        }

    def status(self):
        return {
            "running": self.running,
        }


class FakePersistence:
    def __init__(self):
        self.state = None

    def load(self):
        return self.state

    def save(self, state):
        self.state = state


def test_startup():
    lifecycle = FactoryLifecycle(
        FakeDaemon(),
        FakePersistence(),
    )

    result = lifecycle.startup()

    assert result["startup"]["status"] == "started"


def test_shutdown_saves_state():
    persistence = FakePersistence()

    lifecycle = FactoryLifecycle(
        FakeDaemon(),
        persistence,
    )

    lifecycle.shutdown(
        {
            "version": 1,
        }
    )

    assert persistence.state["version"] == 1


def test_recover():
    persistence = FakePersistence()
    persistence.state = {
        "version": 2,
    }

    lifecycle = FactoryLifecycle(
        FakeDaemon(),
        persistence,
    )

    result = lifecycle.recover()

    assert result["recovered"] is True
    assert result["state"]["version"] == 2
