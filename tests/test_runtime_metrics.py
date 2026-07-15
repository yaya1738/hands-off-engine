from ai.factory.runtime_metrics import (
    FactoryRuntimeMetrics,
)


def test_increment():
    metrics = FactoryRuntimeMetrics()

    result = metrics.increment(
        "cycles"
    )

    assert result["cycles"] == 1


def test_record_success():
    metrics = FactoryRuntimeMetrics()

    result = metrics.record(
        True
    )

    assert result["metrics"]["successes"] == 1


def test_record_failure():
    metrics = FactoryRuntimeMetrics()

    result = metrics.record(
        False
    )

    assert result["metrics"]["failures"] == 1


def test_snapshot():
    metrics = FactoryRuntimeMetrics()

    metrics.record(True)

    result = metrics.snapshot()

    assert result["cycles"] == 1


def test_history():
    metrics = FactoryRuntimeMetrics()

    metrics.record(True)

    assert len(metrics.history()) > 0
