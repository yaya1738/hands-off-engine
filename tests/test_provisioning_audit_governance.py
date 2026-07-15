from ai.audit.provisioning_audit_governance import (
    ProvisioningAuditGovernance,
)


def test_governance_record_creation():
    governance = ProvisioningAuditGovernance()

    result = governance.create(
        {"status": "PASS"},
        {"snapshot_id": "abc"},
        {"passed": True},
        {"owner": "audit"},
    )

    assert result["governance_type"] == "provisioning_audit"
    assert result["status"] == "PASS"
    assert result["snapshot"]["snapshot_id"] == "abc"


def test_governance_defaults_metadata():
    governance = ProvisioningAuditGovernance()

    result = governance.create(
        {"status": "FAIL"},
        {},
        {},
    )

    assert result["metadata"] == {}
