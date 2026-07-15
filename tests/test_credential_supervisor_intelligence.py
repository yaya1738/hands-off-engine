from autonomous.credentials.intelligence.supervisor_intelligence import (
    SupervisorIntelligence,
)


def test_supervisor_intelligence():

    result = SupervisorIntelligence().generate(
        {
            "diagnosis":
            "authorization_consent_required",
            "confidence":
            0.83,
        }
    )

    assert result["component"] == "credential_supervisor"
    assert result["actions_allowed"] is False
    assert result["mode"] == "read_only"
