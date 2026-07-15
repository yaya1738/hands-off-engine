from ai.factory.result_metrics import (
    ResultMetrics,
)


def test_calculate_metrics():
    metrics = ResultMetrics()

    result = metrics.calculate(
        [
            {
                "status": "SUCCESS",
            },
            {
                "status": "FAILED",
            },
        ]
    )

    assert result["jobs_total"] == 2
    assert result["jobs_successful"] == 1
    assert result["jobs_failed"] == 1
    assert result["success_rate"] == 0.5


def test_empty_results():
    metrics = ResultMetrics()

    result = metrics.calculate([])

    assert result["jobs_total"] == 0
    assert result["success_rate"] == 0


def test_rate_helpers():
    metrics = ResultMetrics()

    results = [
        {
            "status": "SUCCESS",
        }
    ]

    assert metrics.success_rate(results) == 1
    assert metrics.failure_rate(results) == 0
