from ai.factory.runtime_dashboard import (
    FactoryRuntimeDashboard,
)


def fake_health():
    return {
        "status": "HEALTHY",
    }


def fake_audit():
    return [
        {
            "type": "EVENT",
        }
    ]


def build():
    return FactoryRuntimeDashboard(
        health=fake_health,
        audit=fake_audit,
    )


def test_snapshot():
    dashboard = build()

    result = dashboard.snapshot()

    assert result["health"]["status"] == "HEALTHY"


def test_summary():
    dashboard = build()

    result = dashboard.summary()

    assert result["event_count"] == 1


def test_history():
    dashboard = build()

    dashboard.snapshot()

    assert len(dashboard.records()) == 1
