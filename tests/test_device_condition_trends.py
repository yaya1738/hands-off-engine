from datetime import datetime, timezone

from scripts.device_condition_trends import summarize_device_condition

NOW = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)


def obs(minutes_ago, snapshot, assessment=None):
    from datetime import timedelta
    return {
        "observed_at": (NOW - timedelta(minutes=minutes_ago)).isoformat(),
        "snapshot": snapshot,
        "assessment": assessment or {},
    }


def test_unknown_when_no_valid_observations_and_no_health_claim():
    result = summarize_device_condition(
        [{"observed_at": "not-a-date", "snapshot": {"battery_percent": 99}}],
        now=NOW,
    )
    assert result["status"] == "unknown"
    assert result["latest_observed_at"] is None
    assert result["metrics"] == {}
    assert result["advisory_only"] is True


def test_stale_observation_is_explicit_not_healthy():
    result = summarize_device_condition([obs(60, {"battery_percent": 90})],
                                        now=NOW, max_age_seconds=300)
    assert result["status"] == "stale"
    assert result["age_seconds"] == 3600
    assert result["metrics"]["battery_percent"]["latest"] == 90


def test_recent_observations_produce_bounded_metric_summary():
    result = summarize_device_condition(
        [obs(10, {"battery_percent": 80}), obs(5, {"battery_percent": 60})],
        now=NOW, max_age_seconds=900, window_seconds=3600,
    )
    assert result["status"] == "fresh"
    assert result["observations_in_window"] == 2
    assert result["metrics"]["battery_percent"] == {
        "samples": 2, "latest": 60.0, "minimum": 60.0,
        "maximum": 80.0, "mean": 70.0,
    }


def test_repeated_thermal_pressure_is_counted():
    result = summarize_device_condition([
        obs(20, {"temperature_c": 43}),
        obs(10, {"temperature_c": 38}, {"warnings": ["elevated_temperature"]}),
        obs(5, {"temperature_c": None}, {"concerns": ["high_temperature"]}),
    ], now=NOW, window_seconds=3600)
    assert result["thermal_events_in_window"] == 3


def test_manual_defects_require_timestamp_and_provenance():
    result = summarize_device_condition(
        [obs(1, {"battery_percent": 50})], now=NOW,
        manual_reports=[
            {"reported_at": NOW.isoformat(), "defect": "thermal shutdown",
             "reported_by": "operator", "source": "user_report"},
            {"reported_at": NOW.isoformat(), "defect": "no provenance"},
        ],
    )
    assert len(result["manual_defects"]) == 1
    assert result["manual_defects"][0]["reported_by"] == "operator"


def test_future_observations_are_ignored():
    result = summarize_device_condition(
        [{"observed_at": "2026-10-15T13:00:00+00:00",
          "snapshot": {"battery_percent": 100}}], now=NOW)
    assert result["status"] == "unknown"
    assert result["observations_in_window"] == 0


def test_naive_now_is_rejected():
    try:
        summarize_device_condition([], now=datetime(2026, 10, 15, 12, 0))
    except ValueError as exc:
        assert "timezone-aware" in str(exc)
    else:
        raise AssertionError("expected timezone validation")



def test_additional_observed_health_metrics_are_summarized_without_imputation():
    result = summarize_device_condition(
        [obs(1, {"cpu_load_percent": 75, "cpu_throttling_percent": 20,
                 "network_quality_percent": None, "io_error_count": 3})],
        now=NOW,
    )
    assert result["metrics"]["cpu_load_percent"]["latest"] == 75
    assert result["metrics"]["cpu_throttling_percent"]["latest"] == 20
    assert result["metrics"]["io_error_count"]["latest"] == 3
    assert "network_quality_percent" not in result["metrics"]


def test_assessment_resource_pressure_events_are_counted():
    result = summarize_device_condition(
        [obs(2, {"battery_percent": 20},
             {"warnings": ["battery_low"], "concerns": ["memory_pressure"]})],
        now=NOW,
    )
    assert result["resource_pressure_events_in_window"] == 2
    assert result["concern_counts"]["memory_pressure"] == 1
    assert result["warning_counts"]["battery_low"] == 1
