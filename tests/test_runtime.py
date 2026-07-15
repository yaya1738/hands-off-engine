from ai.factory.runtime import (
    FactoryRuntime,
)


class FakeBootstrap:
    def start(self):
        return {
            "status": "STARTED",
        }


class FakeControl:
    def cycle(self, state):
        return {
            "cycle": True,
        }


def build():
    return FactoryRuntime(
        bootstrap=FakeBootstrap(),
        control_plane=FakeControl(),
    )


def test_start():
    runtime = build()

    result = runtime.start()

    assert result["status"] == "RUNNING"


def test_run():
    runtime = build()

    result = runtime.run({})

    assert result["cycle"] == 1


def test_heartbeat():
    runtime = build()

    runtime.start()

    result = runtime.heartbeat()

    assert result["running"] is True


def test_stop():
    runtime = build()

    result = runtime.stop()

    assert result["status"] == "STOPPED"


def test_history():
    runtime = build()

    runtime.start()

    assert len(runtime.history()) == 1
