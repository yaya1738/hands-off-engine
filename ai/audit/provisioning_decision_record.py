from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class ProvisioningDecisionRecord:
    decision_id: str
    request_id: str
    requester_identity: str
    estimated_cost: float
    decision: str
    reason: str
    policy_id: str
    policy_version: str
    policy_hash: str
    evidence: Dict[str, Any]
    replay_match: bool
    timestamp: str


def create_decision_record(
    decision_id: str,
    request_id: str,
    requester_identity: str,
    estimated_cost: float,
    decision: str,
    reason: str,
    policy_id: str,
    policy_version: str,
    policy_hash: str,
    evidence: Dict[str, Any],
    replay_match: bool,
) -> ProvisioningDecisionRecord:
    return ProvisioningDecisionRecord(
        decision_id=decision_id,
        request_id=request_id,
        requester_identity=requester_identity,
        estimated_cost=estimated_cost,
        decision=decision,
        reason=reason,
        policy_id=policy_id,
        policy_version=policy_version,
        policy_hash=policy_hash,
        evidence=evidence,
        replay_match=replay_match,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
