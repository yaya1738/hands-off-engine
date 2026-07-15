from ai.factory.improvement_optimizer import (
    FactoryImprovementOptimizer,
)


def test_score():
    optimizer = FactoryImprovementOptimizer()

    result = optimizer.score(
        {
            "impact": 1,
            "success_rate": 1,
            "risk": 0,
        }
    )

    assert result["score"] == 1


def test_rank():
    optimizer = FactoryImprovementOptimizer()

    result = optimizer.rank(
        [
            {
                "impact": 0.2,
                "success_rate": 0.2,
            },
            {
                "impact": 0.9,
                "success_rate": 0.9,
            },
        ]
    )

    assert result[0]["improvement"]["impact"] == 0.9


def test_select():
    optimizer = FactoryImprovementOptimizer()

    result = optimizer.select(
        [
            {
                "impact": 1,
                "success_rate": 1,
            }
        ]
    )

    assert result is not None


def test_history():
    optimizer = FactoryImprovementOptimizer()

    optimizer.score(
        {
            "impact": 1,
        }
    )

    assert len(optimizer.history()) == 1
