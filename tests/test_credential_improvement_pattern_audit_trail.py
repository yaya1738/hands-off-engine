from autonomous.credentials.intelligence.improvement_pattern_audit_trail import (
    IntelligenceImprovementPatternAuditTrail,
)


def test_audit():

    result = IntelligenceImprovementPatternAuditTrail().record(
        {
            "recommendation":
            "prioritize_pattern_feedback_learning",
            "confidence":
            0.85,
        }
    )

    assert result["event"] == (
        "improvement_pattern_recommendation_generated"
    )
    assert result["confidence"] == 0.85
    assert result["mode"] == "read_only"
