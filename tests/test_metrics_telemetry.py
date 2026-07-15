from ai.factory.metrics_telemetry import (
    FactoryMetricsTelemetry,
)


def build():
    return FactoryMetricsTelemetry()


def test_record_metric():
    telemetry = build()

    result = telemetry.record_metric(
        "speed",
        10,
    )

    assert result["recorded"] is True


def test_track_event():
    telemetry = build()

    result = telemetry.track_event(
        {
            "type": "RUN",
        }
    )

    assert result["tracked"] is True


def test_calculate_health():
    telemetry = build()

    result = telemetry.calculate_health()

    assert result["health"] == "GOOD"


def test_dashboard():
    telemetry = build()

    result = telemetry.dashboard()

    assert "metrics" in result


def test_history():
    telemetry = build()

    telemetry.record_metric(
        "x",
        1,
    )

    assert len(telemetry.history()) == 1
