from ai.factory.self_assessment import (
    FactorySelfAssessment,
)


def test_assess():
    engine = FactorySelfAssessment()

    result = engine.assess(
        {
            "success_rate": 0.9,
            "average_impact": 0.5,
        }
    )

    assert result["health"] == 0.9


def test_detect_gaps():
    engine = FactorySelfAssessment()

    result = engine.detect_gaps(
        {
            "success_rate": 0.5,
            "average_impact": 0.1,
        }
    )

    assert len(result) == 2


def test_recommend():
    engine = FactorySelfAssessment()

    result = engine.recommend(
        {
            "gaps": [
                "slow recovery",
            ]
        }
    )

    assert "improve slow recovery" in result


def test_history():
    engine = FactorySelfAssessment()

    engine.assess(
        {
            "success_rate": 1,
        }
    )

    assert len(engine.history()) == 1
