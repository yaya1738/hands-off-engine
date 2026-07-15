from ai.audit.provisioning_integrity_verifier import (
    ProvisioningIntegrityVerifier,
)
from ai.audit.provisioning_decision_record import (
    create_decision_record,
)


def test_valid_record_passes_integrity_check():
    record = create_decision_record(
        "decision-1",
        "request-1",
        "agent",
        10,
        "AUDIT_ONLY",
        "within_policy",
        "policy",
        "v1",
        "hash",
        {"cost": 10},
        True,
    )

    result = ProvisioningIntegrityVerifier().verify(record)

    assert result.valid is True
    assert result.issues == []


def test_invalid_replay_fails_integrity_check():
    record = create_decision_record(
        "decision-2",
        "request-2",
        "agent",
        10,
        "DENY",
        "reason",
        "policy",
        "v1",
        "hash",
        {"cost": 10},
        False,
    )

    result = ProvisioningIntegrityVerifier().verify(record)

    assert result.valid is False
    assert "replay_consistent" in result.issues
