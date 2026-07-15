from ai.factory.metrics_intelligence import (
    FactoryMetricsIntelligence,
)


def build():
    return FactoryMetricsIntelligence()


def test_record_metric():
    engine = build()

    result = engine.record_metric(
        {}
    )

    assert result["recorded"] is True


def test_aggregate_metrics():
    engine = build()

    result = engine.aggregate_metrics()

    assert result["aggregated"] is True


def test_analyze_trends():
    engine = build()

    result = engine.analyze_trends()

    assert result["analyzed"] is True


def test_detect_anomaly():
    engine = build()

    result = engine.detect_anomaly(
        {}
    )

    assert result["detected"] is True


def test_history():
    engine = build()

    engine.record_metric(
        {}
    )

    assert len(engine.history()) == 1
