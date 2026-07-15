from ai.factory.health import FactoryHealth


def test_factory_is_healthy():
    health = FactoryHealth()

    result = health.check(
        registry={},
        memory=[],
        state={},
    )

    assert result["status"] == "HEALTHY"
    assert result["checks"]["registry"] is True


def test_factory_degraded():
    health = FactoryHealth()

    result = health.check(
        registry={},
        memory=None,
        state={},
    )

    assert result["status"] == "DEGRADED"
    assert result["checks"]["memory"] is False
