from autonomous.credentials.intelligence.priority import (
    CredentialPriorityResolver,
)


def test_priority_overrides_common_signal():

    result = CredentialPriorityResolver().resolve(
        [
            {
                "diagnosis":
                "no_known_anomaly",
                "confidence":
                0.95,
            },
            {
                "diagnosis":
                "authorization_consent_required",
                "confidence":
                0.80,
            },
        ]
    )

    assert (
        result["primary_diagnosis"]
        ==
        "authorization_consent_required"
    )

    assert result["mode"] == "read_only"
