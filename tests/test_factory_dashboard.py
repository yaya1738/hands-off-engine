from ai.factory.dashboard import FactoryDashboard


def test_dashboard_snapshot():
    dashboard = FactoryDashboard()

    result = dashboard.snapshot(
        {
            "status": "HEALTHY",
        },
        [
            "planner",
            "runner",
        ],
        {
            "total": 2,
            "success": 2,
        },
        {
            "mode": "active",
        },
    )

    assert result["health"]["status"] == "HEALTHY"
    assert len(result["components"]) == 2
    assert result["telemetry"]["success"] == 2
    assert result["state"]["mode"] == "active"
