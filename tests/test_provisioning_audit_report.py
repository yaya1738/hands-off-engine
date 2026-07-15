from ai.audit.provisioning_audit_report import (
    ProvisioningAuditReport,
)


def test_report_pass():
    report = ProvisioningAuditReport().generate(
        {
            "issues": [],
            "total_records": 1,
        },
        {
            "complete": True,
        },
    )

    assert report["status"] == "PASS"
    assert report["report_type"] == "provisioning_audit"


def test_report_fail_on_missing_evidence():
    report = ProvisioningAuditReport().generate(
        {
            "issues": [],
        },
        {
            "complete": False,
        },
    )

    assert report["status"] == "FAIL"
