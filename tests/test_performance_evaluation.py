from ai.factory.performance_evaluation import (
    FactoryPerformanceEvaluation,
)


def build():
    return FactoryPerformanceEvaluation()


def test_evaluate_action():
    evaluator = build()

    result = evaluator.evaluate_action(
        {
            "action": "RUN",
        }
    )

    assert result["evaluated"] is True


def test_measure_impact():
    evaluator = build()

    result = evaluator.measure_impact(
        {},
        {},
    )

    assert result["impact_measured"] is True


def test_compare_results():
    evaluator = build()

    result = evaluator.compare_results(
        {
            "x": 1,
        },
        {
            "x": 1,
        },
    )

    assert result["matched"] is True


def test_score_performance():
    evaluator = build()

    result = evaluator.score_performance(
        {}
    )

    assert result["score"] == 1


def test_history():
    evaluator = build()

    evaluator.evaluate_action({})

    assert len(evaluator.history()) == 1
