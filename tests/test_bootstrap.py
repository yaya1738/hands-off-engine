from ai.factory.bootstrap import (
    FactoryBootstrap,
)


class FakeControl:
    def start(self):
        return {
            "status": "STARTED",
        }


def build():
    return FactoryBootstrap(
        control_plane=FakeControl()
    )


def test_initialize():
    factory = build()

    result = factory.initialize()

    assert result["status"] == "INITIALIZED"


def test_start():
    factory = build()

    result = factory.start()

    assert result["status"] == "STARTED"


def test_status():
    factory = build()

    factory.start()

    result = factory.status()

    assert result["running"] is True


def test_shutdown():
    factory = build()

    result = factory.shutdown()

    assert result["status"] == "STOPPED"


def test_history():
    factory = build()

    factory.initialize()

    assert len(factory.history()) == 1
