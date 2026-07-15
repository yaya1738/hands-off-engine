from autonomous.credentials.intelligence.decision_context import (
    DecisionContextBuilder,
)


def test_context():

    result = DecisionContextBuilder().build(
        "attention_required",
        "authorization_consent_required",
        0.83,
        [
            "external_consent_requested"
        ],
        {
            "historical_support":
            1.0
        },
        {
            "actions_allowed":
            False
        },
    )

    assert result["context"] == "credential_bridge"
    assert result["mode"] == "read_only"
