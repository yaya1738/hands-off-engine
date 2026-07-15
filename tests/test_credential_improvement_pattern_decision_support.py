from autonomous.credentials.intelligence.improvement_pattern_decision_support import (
    IntelligenceImprovementPatternDecisionSupport,
)


def test_decision():

    result = IntelligenceImprovementPatternDecisionSupport().decide(
        {
            "context_quality": "enhanced",
            "reliability": 1.0,
        }
    )

    assert result["recommendation"] == (
        "prioritize_pattern_feedback_learning"
    )
    assert result["priority"] == "medium"
    assert result["confidence"] == 0.85
    assert result["mode"] == "read_only"
