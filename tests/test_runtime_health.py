from ai.factory.runtime_health import (
    FactoryRuntimeHealth,
)


def test_collect():
    monitor = FactoryRuntimeHealth()

    result = monitor.collect(
        {
            "cycles": 5,
            "errors": 0,
            "running": True,
        }
    )

    assert result["cycles"] == 5


def test_healthy():
    monitor = FactoryRuntimeHealth()

    result = monitor.status(
        {
            "cycles": 1,
            "errors": 0,
            "running": True,
        }
    )

    assert result["status"] == "HEALTHY"


def test_degraded():
    monitor = FactoryRuntimeHealth()

    result = monitor.status(
        {
            "cycles": 1,
            "errors": 1,
            "running": True,
        }
    )

    assert result["status"] == "DEGRADED"


def test_history():
    monitor = FactoryRuntimeHealth()

    monitor.collect({})

    assert len(monitor.history()) == 1
