from autonomous.credentials.intelligence.context_validator import (
    ContextValidator,
)


def test_validator():

    result = ContextValidator().validate(
        {
            "context":
            "credential_bridge",

            "situation":
            "attention_required",

            "diagnosis":
            "authorization_consent_required",

            "confidence":
            0.83,

            "safety":
            {
                "actions_allowed":
                False
            },

            "mode":
            "read_only",
        }
    )

    assert result["valid"] is True
    assert result["safety_verified"] is True
    assert result["mode"] == "read_only"
