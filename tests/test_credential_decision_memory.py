from autonomous.credentials.intelligence.decision_memory import (
    DecisionMemory,
)


def test_decision_memory():

    memory = DecisionMemory()

    result = memory.record(
        "authorization_consent_required",
        "await_user_authorization",
        0.835,
        "resolved",
    )

    assert result["outcome"] == "resolved"
    assert result["mode"] == "read_only"
