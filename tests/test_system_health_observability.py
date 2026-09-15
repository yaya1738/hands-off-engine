from scripts.system_health_observability import project_system_health


def test_projects_bounded_health_observation():
    result = project_system_health({
        "status": "warn",
        "generated_at": "2026-09-15T00:00:00+00:00",
        "components": {"scheduler": "ok", "pipeline": "warn"},
        "checks": {
            "latest_snapshot_age_sec": 10,
            "latest_fetch_age_sec": 20,
            "num_snapshots": 5,
            "recent_error_rate": 0.2,
            "most_recent_run_status": "ok",
        },
        "errors": ["degraded"],
        "secret": "excluded",
    })

    assert result["available"] is True
    assert result["status"] == "warn"
    assert result["components"]["pipeline"] == "warn"
    assert result["checks"]["recent_error_rate"] == 0.2
    assert result["error_count"] == 1
    assert "secret" not in str(result)


def test_malformed_health_fails_closed():
    assert project_system_health(None) == {"available": False}


def test_missing_sections_are_bounded():
    result = project_system_health({"status": "ok"})
    assert result["available"] is True
    assert result["components"] == {}
    assert result["checks"]["num_snapshots"] == 0
    assert result["error_count"] == 0
