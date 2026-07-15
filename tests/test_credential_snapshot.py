from autonomous.credentials.intelligence.snapshot import (
    IntelligenceSnapshot,
)


def test_snapshot():

    result = IntelligenceSnapshot().create(
        {
            "status":
            "attention_required",
            "diagnosis":
            "authorization_consent_required",
            "confidence":
            0.83,
            "recommendation":
            "await_user_authorization",
        }
    )

    assert result["system"] == "credential_bridge"
    assert result["confidence"] == 0.83
    assert result["safety_mode"] == "read_only"
