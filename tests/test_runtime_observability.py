from ai.factory.runtime_observability import (
    FactoryRuntimeObservability,
)


def build():
    return FactoryRuntimeObservability()


def test_record_metric():
    engine = build()

    result = engine.record_metric(
        {}
    )

    assert result["recorded"] is True


def test_capture_health():
    engine = build()

    result = engine.capture_health(
        {}
    )

    assert result["captured"] is True


def test_detect_anomaly():
    engine = build()

    result = engine.detect_anomaly(
        {}
    )

    assert result["detected"] is True


def test_generate_alert():
    engine = build()

    result = engine.generate_alert(
        {}
    )

    assert result["generated"] is True


def test_history():
    engine = build()

    engine.record_metric(
        {}
    )

    assert len(engine.history()) == 1
