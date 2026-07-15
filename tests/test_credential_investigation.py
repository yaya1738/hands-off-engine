from autonomous.credentials.intelligence.investigation import (
    CredentialInvestigationPlanner,
)


def test_investigation_priority():

    result = CredentialInvestigationPlanner().plan(
        [
            "provider_response",
            "authorization_completion_confirmation"
        ]
    )

    assert (
        result[0]["investigation"]
        ==
        "authorization_completion_confirmation"
    )

    assert result[0]["mode"] == "read_only"
