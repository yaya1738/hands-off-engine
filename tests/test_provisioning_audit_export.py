from ai.audit.provisioning_audit_export import (
    ProvisioningAuditExporter,
)
from ai.audit.provisioning_decision_record import (
    create_decision_record,
)


def test_audit_export_preserves_record():
    record = create_decision_record(
        "decision-1",
        "request-1",
        "agent",
        25,
        "AUDIT_ONLY",
        "within_policy",
        "policy",
        "v1",
        "hash",
        {"cost": 25},
        True,
    )

    exported = ProvisioningAuditExporter().export(record)

    assert exported["decision_id"] == "decision-1"
    assert exported["policy_hash"] == "hash"
    assert exported["evidence"]["cost"] == 25
    assert exported["replay_match"] is True
