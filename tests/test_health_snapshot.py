from ai.factory.health_snapshot import (
    FactoryHealthSnapshot,
)


def test_healthy():
    system = FactoryHealthSnapshot()

    result = system.collect(
        {
            "scheduler": "HEALTHY",
            "executor": "HEALTHY",
        }
    )

    assert result["health"] == "HEALTHY"
    assert result["issues"] == []


def test_degraded():
    system = FactoryHealthSnapshot()

    result = system.collect(
        {
            "scheduler": "FAILED",
        }
    )

    assert result["health"] == "DEGRADED"
    assert "scheduler" in result["issues"]


def test_status():
    system = FactoryHealthSnapshot()

    assert system.status(
        {
            "worker": "HEALTHY",
        }
    ) == "HEALTHY"


def test_history():
    system = FactoryHealthSnapshot()

    system.collect(
        {
            "worker": "HEALTHY",
        }
    )

    assert len(system.history()) == 1
