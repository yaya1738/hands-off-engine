from autonomous.credentials.intelligence.health_monitor import (
    IntelligenceHealthMonitor,
)


def test_health():

    result = IntelligenceHealthMonitor().assess(
        {
            "stability_score":
            0.72
        },
        "declining",
    )

    assert result["health"] == "degraded"
    assert result["mode"] == "read_only"
