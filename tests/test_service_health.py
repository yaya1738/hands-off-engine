from ai.factory.service_health import (
    FactoryServiceHealth,
)


class FakeService:
    def heartbeat(self):
        return {
            "running": True,
        }


def build():
    return FactoryServiceHealth(
        FakeService()
    )


def test_heartbeat():
    health = build()

    result = health.heartbeat()

    assert result["running"] is True


def test_check():
    health = build()

    result = health.check()

    assert result["healthy"] is True


def test_ready():
    health = build()

    result = health.ready()

    assert result["ready"] is True


def test_history():
    health = build()

    health.check()

    assert len(health.history()) == 2
