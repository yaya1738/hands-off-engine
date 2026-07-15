from autonomous.credentials.intelligence.improvement_decision_support import (
    IntelligenceImprovementDecisionSupport,
)


def test_decision():

    result = IntelligenceImprovementDecisionSupport().decide(
        {
            "context_quality": "enhanced",
        }
    )

    assert result["recommendation"] == (
        "prioritize_confidence_tracking"
    )
    assert result["priority"] == "medium"
    assert result["mode"] == "read_only"
