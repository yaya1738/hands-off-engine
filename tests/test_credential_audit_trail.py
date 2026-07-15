from autonomous.credentials.intelligence.audit_trail import (
    IntelligenceAuditTrail,
)


def test_audit():

    audit = IntelligenceAuditTrail()

    result = audit.record(
        {
            "decision": "human_review_priority",
            "risk": "high",
            "confidence": 0.69,
        }
    )

    assert result["decision"] == "human_review_priority"
    assert result["risk"] == "high"
    assert result["mode"] == "read_only"
