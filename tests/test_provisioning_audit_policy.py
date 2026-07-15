from types import SimpleNamespace

from ai.audit.provisioning_audit_policy import (
    ProvisioningAuditPolicy,
)


def test_policy_pass():
    policy = ProvisioningAuditPolicy()

    result = policy.evaluate(
        {"complete": True},
        SimpleNamespace(valid=True),
        SimpleNamespace(valid=True),
    )

    assert result["compliant"] is True
    assert result["findings"] == []


def test_policy_detects_failures():
    policy = ProvisioningAuditPolicy()

    result = policy.evaluate(
        {"complete": False},
        SimpleNamespace(valid=False),
        SimpleNamespace(valid=False),
    )

    assert result["compliant"] is False
    assert "incomplete_evidence" in result["findings"]
    assert "integrity_failure" in result["findings"]
    assert "consistency_failure" in result["findings"]
