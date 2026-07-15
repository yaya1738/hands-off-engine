from types import SimpleNamespace

from ai.audit.provisioning_audit_summary import (
    ProvisioningAuditSummary,
)


def test_summary_counts_decisions():
    summary = ProvisioningAuditSummary()

    records = [
        SimpleNamespace(decision="AUDIT_ONLY"),
        SimpleNamespace(decision="DENY"),
        SimpleNamespace(decision="APPROVAL_QUEUE"),
    ]

    result = summary.summarize(records)

    assert result["total_records"] == 3
    assert result["decisions"]["AUDIT_ONLY"] == 1
    assert result["decisions"]["DENY"] == 1
    assert result["decisions"]["APPROVAL_QUEUE"] == 1


def test_summary_collects_issues():
    summary = ProvisioningAuditSummary()

    result = summary.summarize(
        [],
        integrity_results=[
            SimpleNamespace(valid=False, issues=["hash_mismatch"])
        ],
    )

    assert "hash_mismatch" in result["issues"]
