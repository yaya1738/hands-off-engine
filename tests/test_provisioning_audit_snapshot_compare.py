from ai.audit.provisioning_audit_snapshot_compare import (
    ProvisioningAuditSnapshotCompare,
)


def test_identical_snapshots():
    comparator = ProvisioningAuditSnapshotCompare()

    result = comparator.compare(
        {"status": "PASS"},
        {"status": "PASS"},
    )

    assert result["changed"] is False
    assert result["differences"] == []


def test_changed_snapshot_detected():
    comparator = ProvisioningAuditSnapshotCompare()

    result = comparator.compare(
        {"status": "PASS"},
        {"status": "FAIL"},
    )

    assert result["changed"] is True
    assert result["differences"][0]["field"] == "status"
