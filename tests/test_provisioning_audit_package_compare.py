from ai.audit.provisioning_audit_package_compare import (
    ProvisioningAuditPackageCompare,
)


def test_identical_packages():
    comparator = ProvisioningAuditPackageCompare()

    result = comparator.compare(
        {"status": "PASS"},
        {"status": "PASS"},
    )

    assert result["changed"] is False
    assert result["differences"] == []


def test_changed_package_detected():
    comparator = ProvisioningAuditPackageCompare()

    result = comparator.compare(
        {"status": "PASS"},
        {"status": "FAIL"},
    )

    assert result["changed"] is True
    assert result["differences"][0]["section"] == "status"
