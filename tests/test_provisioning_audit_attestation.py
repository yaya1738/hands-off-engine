from ai.audit.provisioning_audit_attestation import (
    ProvisioningAuditAttestation,
)


def test_attestation_creation():
    attestation = ProvisioningAuditAttestation()

    result = attestation.create(
        {"status": "PASS"},
        "audit_engine",
    )

    assert result["attestation_type"] == "provisioning_audit"
    assert result["status"] == "PASS"
    assert result["auditor"] == "audit_engine"
    assert result["attested"] is True


def test_default_auditor():
    attestation = ProvisioningAuditAttestation()

    result = attestation.create(
        {"status": "FAIL"},
    )

    assert result["auditor"] == "system"
