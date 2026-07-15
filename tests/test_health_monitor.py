from ai.factory.health_monitor import (
    FactoryHealthMonitor,
)


def test_healthy():
    monitor = FactoryHealthMonitor(
        {
            "runtime": lambda: True,
            "state": lambda: True,
        }
    )

    result = monitor.check()

    assert result["health"] == "HEALTHY"
    assert result["issues"] == []


def test_degraded():
    monitor = FactoryHealthMonitor(
        {
            "runtime": lambda: False,
        }
    )

    result = monitor.check()

    assert result["health"] == "DEGRADED"
    assert "runtime" in result["issues"]


def test_alerts():
    monitor = FactoryHealthMonitor(
        {
            "scheduler": lambda: False,
        }
    )

    monitor.check()

    assert monitor.alerts() == [
        "scheduler"
    ]
