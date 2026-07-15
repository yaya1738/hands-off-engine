from typing import Any, Dict


class ProvisioningAuditGovernance:
    def create(
        self,
        report: Dict[str, Any],
        snapshot: Dict[str, Any],
        controls: Dict[str, Any],
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        return {
            "governance_type": "provisioning_audit",
            "status": report.get("status", "UNKNOWN"),
            "report": report,
            "snapshot": snapshot,
            "controls": controls,
            "metadata": metadata or {},
        }
