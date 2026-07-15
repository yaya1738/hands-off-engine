from ai.audit.provisioning_audit_snapshot import (
    ProvisioningAuditSnapshot,
)


def test_snapshot_creation():
    snapshot = ProvisioningAuditSnapshot().create(
        [],
        {"complete": True},
        {"issues": []},
        {"status": "PASS"},
    )

    assert snapshot["snapshot_id"]
    assert snapshot["evidence"]["complete"] is True


def test_snapshot_is_deterministic():
    manager = ProvisioningAuditSnapshot()

    first = manager.create(
        [],
        {"complete": True},
        {"issues": []},
        {"status": "PASS"},
    )

    second = manager.create(
        [],
        {"complete": True},
        {"issues": []},
        {"status": "PASS"},
    )

    assert first["snapshot_id"] == second["snapshot_id"]
