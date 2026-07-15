from autonomous.credentials.intelligence.knowledge import (
    CredentialKnowledgeBase,
)


def test_known_pattern():

    result = CredentialKnowledgeBase().analyze(
        [
            "adapter_requires_external_consent",
            "REQUESTED->AWAITING_AUTHORIZATION"
        ]
    )

    assert result["mode"] == "read_only"
    assert (
        result["knowledge_matches"][0]["diagnosis"]
        ==
        "authorization_consent_required"
    )
