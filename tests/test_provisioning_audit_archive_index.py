from ai.audit.provisioning_audit_archive_index import (
    ProvisioningAuditArchiveIndex,
)


def test_find_by_package_id():
    index = ProvisioningAuditArchiveIndex()

    index.add(
        {
            "package_id": "pkg-1",
            "hash": "abc",
            "status": "PASS",
        }
    )

    result = index.find_by_id("pkg-1")

    assert len(result) == 1
    assert result[0]["hash"] == "abc"


def test_find_by_status():
    index = ProvisioningAuditArchiveIndex()

    index.add(
        {
            "package_id": "pkg-2",
            "status": "FAIL",
        }
    )

    result = index.find_by_status("FAIL")

    assert len(result) == 1
