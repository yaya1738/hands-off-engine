from ai.factory.improvement_metrics import (
    FactoryImprovementMetrics,
)


def test_record_metric():
    metrics = FactoryImprovementMetrics()

    result = metrics.record_metric(
        {
            "success": True,
            "impact": 0.5,
        }
    )

    assert result["impact"] == 0.5


def test_calculate():
    metrics = FactoryImprovementMetrics()

    metrics.record_metric(
        {
            "success": True,
            "impact": 1,
        }
    )

    metrics.record_metric(
        {
            "success": False,
            "impact": 0,
        }
    )

    result = metrics.calculate()

    assert result["count"] == 2
    assert result["success_rate"] == 0.5


def test_empty():
    metrics = FactoryImprovementMetrics()

    result = metrics.summary()

    assert result["count"] == 0


def test_history():
    metrics = FactoryImprovementMetrics()

    metrics.record_metric(
        {
            "impact": 1,
        }
    )

    assert len(metrics.history()) == 1
