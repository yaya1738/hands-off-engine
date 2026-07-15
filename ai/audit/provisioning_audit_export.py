from typing import Any, Dict


class ProvisioningAuditExporter:
    def export(self, record: Any) -> Dict[str, Any]:
        return {
            "decision_id": record.decision_id,
            "request_id": record.request_id,
            "requester_identity": record.requester_identity,
            "estimated_cost": record.estimated_cost,
            "decision": record.decision,
            "reason": record.reason,
            "policy_id": record.policy_id,
            "policy_version": record.policy_version,
            "policy_hash": record.policy_hash,
            "evidence": record.evidence,
            "replay_match": record.replay_match,
            "timestamp": record.timestamp,
        }
