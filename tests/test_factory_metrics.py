from ai.factory.metrics import FactoryMetrics


def test_metrics_calculation():
    metrics = FactoryMetrics()

    result = metrics.calculate(
        [
            {
                "status": "COMPLETE",
            },
            {
                "status": "QUEUED",
            },
        ],
        [
            {
                "id": "artifact-1",
            },
        ],
        [
            {
                "status": "PASS",
            },
            {
                "status": "FAIL",
            },
        ],
    )

    assert result["tasks_total"] == 2
    assert result["tasks_completed"] == 1
    assert result["artifact_count"] == 1
    assert result["verification_pass_rate"] == 0.5


def test_empty_metrics():
    metrics = FactoryMetrics()

    result = metrics.calculate(
        [],
        [],
        [],
    )

    assert result["tasks_total"] == 0
    assert result["verification_pass_rate"] == 0
