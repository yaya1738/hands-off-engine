from ai.audit.provisioning_audit_package_validator import (
    ProvisioningAuditPackageValidator,
)


def test_valid_package():
    validator = ProvisioningAuditPackageValidator()

    result = validator.validate(
        {
            "evidence": {},
            "report": {},
            "snapshot": {},
            "controls": {},
            "governance": {},
            "attestation": {},
        }
    )

    assert result["valid"] is True
    assert result["missing"] == []


def test_missing_sections_detected():
    validator = ProvisioningAuditPackageValidator()

    result = validator.validate(
        {
            "report": {},
        }
    )

    assert result["valid"] is False
    assert "evidence" in result["missing"]
