from autonomous.credentials.intelligence.digest_orchestrator import (
    DigestOrchestrator,
)


def test_digest():

    result = DigestOrchestrator().build(
        "authorization_consent_required",
        0.83,
        100,
        "await_user_authorization",
        [
            "authorization_state_reached"
        ],
        {
            "resolved_before": True
        },
    )

    assert result["system"] == "credential_bridge"
    assert result["status"] == "attention_required"
    assert result["safety"]["oauth_execution"] is False
    assert result["mode"] == "read_only"
