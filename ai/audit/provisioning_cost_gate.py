from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class CostGateDecision(str, Enum):
    AUDIT_ONLY = "AUDIT_ONLY"
    DENY = "DENY"
    APPROVAL_QUEUE = "APPROVAL_QUEUE"


@dataclass
class CostGateResult:
    decision: CostGateDecision
    reason: str
    evidence: Dict[str, Any]


class ProvisioningCostGate:
    def __init__(self, risk_policy: Dict[str, Any]):
        self.risk_policy = risk_policy

    def evaluate(
        self,
        estimated_cost: float,
        available_capital: float,
        requester_identity: str,
    ) -> CostGateResult:
        evidence = {
            "estimated_cost": estimated_cost,
            "available_capital": available_capital,
            "requester_identity": requester_identity,
        }

        if estimated_cost < 0:
            return CostGateResult(
                CostGateDecision.DENY,
                "negative_cost_invalid",
                evidence,
            )

        if available_capital <= 0:
            return CostGateResult(
                CostGateDecision.DENY,
                "insufficient_capital",
                evidence,
            )

        max_allowed = self.risk_policy.get("max_allowed_cost", 1000)
        approval_threshold = self.risk_policy.get("approval_threshold", 100)

        if estimated_cost > max_allowed:
            return CostGateResult(
                CostGateDecision.DENY,
                "cost_exceeds_policy_limit",
                evidence,
            )

        if estimated_cost > approval_threshold:
            return CostGateResult(
                CostGateDecision.APPROVAL_QUEUE,
                "approval_threshold_exceeded",
                evidence,
            )

        return CostGateResult(
            CostGateDecision.AUDIT_ONLY,
            "within_audit_policy",
            evidence,
        )
