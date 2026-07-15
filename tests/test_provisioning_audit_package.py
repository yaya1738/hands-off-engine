from ai.audit.provisioning_audit_package import (
    ProvisioningAuditPackage,
)


def test_package_build():
    package = ProvisioningAuditPackage()

    result = package.build(
        {"complete": True},
        {"status": "PASS"},
        {"snapshot_id": "abc"},
        {"passed": True},
        {"status": "PASS"},
        {"attested": True},
    )

    assert result["package_type"] == "provisioning_audit"
    assert result["report"]["status"] == "PASS"
    assert result["attestation"]["attested"] is True
