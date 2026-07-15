from autonomous.credentials.intelligence.digest_composer import (
    IntelligenceDigestComposer,
)


def test_digest_creation():

    result = IntelligenceDigestComposer().compose(
        "authorization_consent_required",
        0.835,
        [
            "authorization_state_reached"
        ],
        {
            "provider": "gmail",
            "identity_count": 2,
        },
        {
            "priority": 100,
            "severity": "high",
        },
    )

    assert result["diagnosis"] == (
        "authorization_consent_required"
    )

    assert result["impact"]["priority"] == 100
    assert result["mode"] == "read_only"
