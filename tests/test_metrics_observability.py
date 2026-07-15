from ai.factory.metrics_observability import (
    FactoryMetricsObservability,
)


def build():
    return FactoryMetricsObservability()


def test_record_metric():
    metrics = build()

    result = metrics.record_metric(
        {
            "cpu": 50,
        }
    )

    assert result["recorded"] is True


def test_calculate_score():
    metrics = build()

    result = metrics.calculate_score(
        []
    )

    assert result["calculated"] is True


def test_get_dashboard():
    metrics = build()

    result = metrics.get_dashboard()

    assert "metrics" in result


def test_detect_anomaly():
    metrics = build()

    result = metrics.detect_anomaly(
        {}
    )

    assert result["detected"] is True


def test_history():
    metrics = build()

    metrics.record_metric({})

    assert len(metrics.history()) == 1
