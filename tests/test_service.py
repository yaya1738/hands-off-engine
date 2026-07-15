from ai.factory.service import (
    FactoryService,
)


class FakeRuntime:
    def start(self):
        return {
            "status": "RUNNING",
        }

    def stop(self):
        return {
            "status": "STOPPED",
        }

    def heartbeat(self):
        return {
            "running": True,
        }


def build():
    return FactoryService(
        FakeRuntime()
    )


def test_start():
    service = build()

    result = service.start()

    assert result["status"] == "STARTED"


def test_stop():
    service = build()

    result = service.stop()

    assert result["status"] == "STOPPED"


def test_restart():
    service = build()

    result = service.restart()

    assert result["status"] == "RESTARTED"


def test_status():
    service = build()

    service.start()

    assert service.status()["active"] is True


def test_history():
    service = build()

    service.start()

    assert len(service.history()) == 1
