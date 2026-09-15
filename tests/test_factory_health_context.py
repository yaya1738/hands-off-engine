from scripts.factory_health_context import project_factory_health_context


def test_projects_bounded_health_evidence():
    result = project_factory_health_context({
        "status": "warn",
        "generated_at": "2026-09-15T00:00:00+00:00",
        "components": {"pipeline": "warn"},
        "checks": {
            "latest_snapshot_age_sec": 10,
            "latest_fetch_age_sec": 20,
            "recent_error_rate": 0.2,
            "most_recent_run_status": "ok",
        },
        "errors": ["degraded"],
        "secret": "excluded",
    })
    assert result["available"] is True
    assert result["status"] == "warn"
    assert result["error_count"] == 1
    assert result["recent_error_rate"] == 0.2
    assert "secret" not in str(result)


def test_malformed_health_fails_closed():
    assert project_factory_health_context(None) == {"available": False}
