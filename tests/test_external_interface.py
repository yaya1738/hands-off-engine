from ai.factory.external_interface import (
    FactoryExternalInterface,
)


class FakeOrchestrator:
    def start(self):
        return {
            "status": "STARTED",
        }

    def run(self, payload):
        return {
            "cycle": True,
        }

    def status(self):
        return {
            "running": True,
        }


def build():
    return FactoryExternalInterface(
        FakeOrchestrator()
    )


def test_status():
    interface = build()

    result = interface.request(
        "STATUS"
    )

    assert result["running"] is True


def test_start():
    interface = build()

    result = interface.request(
        "START"
    )

    assert result["status"] == "STARTED"


def test_run():
    interface = build()

    result = interface.request(
        "RUN",
        {},
    )

    assert result["cycle"] is True


def test_history():
    interface = build()

    interface.request(
        "STATUS"
    )

    assert len(interface.history()) == 1
