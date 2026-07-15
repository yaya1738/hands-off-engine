from ai.audit.provisioning_decision_record import (
    create_decision_record,
)


def test_decision_record_creation():
    record = create_decision_record(
        "decision-1",
        "request-1",
        "agent",
        25,
        "AUDIT_ONLY",
        "within_policy",
        "cost-policy",
        "v1",
        "hash123",
        {"cost": 25},
        True,
    )

    assert record.decision_id == "decision-1"
    assert record.decision == "AUDIT_ONLY"
    assert record.policy_version == "v1"
    assert record.replay_match is True
    assert record.timestamp
