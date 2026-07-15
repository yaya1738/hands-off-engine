from autonomous.credentials.intelligence.contextual import (
    ContextualPatternEngine,
)


def test_context_cluster():

    result = ContextualPatternEngine().analyze(
        [
            {
                "diagnosis":
                "authorization_consent_required",
                "provider":
                "gmail",
                "identity":
                "user1",
            },
            {
                "diagnosis":
                "authorization_consent_required",
                "provider":
                "gmail",
                "identity":
                "user2",
            },
        ]
    )

    assert result[0]["identity_count"] == 2
    assert result[0]["mode"] == "read_only"
