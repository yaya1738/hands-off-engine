from autonomous.credentials.intelligence.outcome_memory import (
    CredentialOutcomeMemory,
)


def test_outcome_memory():

    memory = CredentialOutcomeMemory()

    memory.record(
        "authorization_consent_required",
        "authorization_completion_confirmation",
        "confirmed"
    )

    result = memory.summarize()

    assert (
        result["authorization_consent_required"]["count"]
        ==
        1
    )
