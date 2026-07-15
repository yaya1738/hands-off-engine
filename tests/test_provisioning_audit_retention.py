from ai.audit.provisioning_audit_retention import (
    ProvisioningAuditRetention,
)


def test_retention_assignment():
    manager = ProvisioningAuditRetention()

    result = manager.assign(
        "decision_record",
        "long_term",
    )

    assert result["artifact_type"] == "decision_record"
    assert result["retention_class"] == "long_term"
    assert result["managed"] is True
