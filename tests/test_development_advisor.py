from ai.factory.development_advisor import (
    FactoryDevelopmentAdvisor,
)


def test_analyze_creates_recommendations():
    advisor = FactoryDevelopmentAdvisor()

    result = advisor.analyze(
        {
            "gaps": [
                "runtime improvement feedback"
            ]
        }
    )

    assert len(result["recommendations"]) == 1
    assert (
        result["recommendations"][0]["requires_approval"]
        is True
    )


def test_history():
    advisor = FactoryDevelopmentAdvisor()

    advisor.analyze(
        {
            "gaps": [
                "test gap"
            ]
        }
    )

    assert len(advisor.history()) == 1
