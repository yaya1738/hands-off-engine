from types import SimpleNamespace

from ai.audit.provisioning_audit_control_matrix import (
    ProvisioningAuditControlMatrix,
)


def test_control_matrix_pass():
    matrix = ProvisioningAuditControlMatrix()

    result = matrix.build(
        SimpleNamespace(valid=True),
        SimpleNamespace(valid=True),
        {"compliant": True},
        {"complete": True},
    )

    assert result["passed"] is True
    assert result["failed_controls"] == []


def test_control_matrix_detects_failure():
    matrix = ProvisioningAuditControlMatrix()

    result = matrix.build(
        SimpleNamespace(valid=False),
        SimpleNamespace(valid=True),
        {"compliant": True},
        {"complete": True},
    )

    assert result["passed"] is False
    assert "integrity" in result["failed_controls"]
