from autonomous.credentials.intelligence.improvement_audit_trail import (
    IntelligenceImprovementAuditTrail,
)


def test_audit():

    trail = IntelligenceImprovementAuditTrail()

    result = trail.record(
        {
            "recommendation":
            "prioritize_confidence_tracking",
            "confidence": 0.85,
        }
    )

    assert result["event"] == (
        "improvement_recommendation_generated"
    )
    assert result["confidence"] == 0.85
    assert result["mode"] == "read_only"
