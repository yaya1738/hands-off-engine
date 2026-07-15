from ai.factory.health_monitor import (
    FactoryHealthMonitor,
)


def test_collect():
    monitor = FactoryHealthMonitor()

    result = monitor.collect(
        {
            "health": "HEALTHY",
        }
    )

    assert result["health"] == "HEALTHY"


def test_detect_change():
    monitor = FactoryHealthMonitor()

    monitor.collect(
        {
            "health": "HEALTHY",
        }
    )

    monitor.collect(
        {
            "health": "DEGRADED",
        }
    )

    result = monitor.detect_change()

    assert result["changed"] is True
    assert result["previous"] == "HEALTHY"
    assert result["current"] == "DEGRADED"


def test_no_change():
    monitor = FactoryHealthMonitor()

    monitor.collect(
        {
            "health": "HEALTHY",
        }
    )

    result = monitor.detect_change()

    assert result["changed"] is False


def test_history():
    monitor = FactoryHealthMonitor()

    monitor.collect(
        {
            "health": "HEALTHY",
        }
    )

    assert len(monitor.history()) == 1
