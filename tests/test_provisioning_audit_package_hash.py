from ai.audit.provisioning_audit_package_hash import (
    ProvisioningAuditPackageHash,
)


def test_hash_created():
    hasher = ProvisioningAuditPackageHash()

    result = hasher.calculate(
        {
            "status": "PASS",
        }
    )

    assert result["algorithm"] == "sha256"
    assert result["hash"]


def test_hash_is_deterministic():
    hasher = ProvisioningAuditPackageHash()

    first = hasher.calculate(
        {
            "status": "PASS",
        }
    )

    second = hasher.calculate(
        {
            "status": "PASS",
        }
    )

    assert first["hash"] == second["hash"]
