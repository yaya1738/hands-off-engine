from ai.audit.provisioning_cost_gate import (
    ProvisioningCostGate,
    CostGateDecision,
)


def test_low_cost_is_audit_only():
    gate = ProvisioningCostGate({"max_allowed_cost": 1000})
    result = gate.evaluate(10, 500, "agent")
    assert result.decision == CostGateDecision.AUDIT_ONLY
    assert result.evidence


def test_medium_cost_requires_approval():
    gate = ProvisioningCostGate({"approval_threshold": 100})
    result = gate.evaluate(200, 500, "agent")
    assert result.decision == CostGateDecision.APPROVAL_QUEUE


def test_excessive_cost_denied():
    gate = ProvisioningCostGate({"max_allowed_cost": 100})
    result = gate.evaluate(200, 500, "agent")
    assert result.decision == CostGateDecision.DENY


def test_no_capital_denied():
    gate = ProvisioningCostGate({})
    result = gate.evaluate(10, 0, "agent")
    assert result.decision == CostGateDecision.DENY


def test_negative_cost_denied():
    gate = ProvisioningCostGate({})
    result = gate.evaluate(-1, 100, "agent")
    assert result.decision == CostGateDecision.DENY
