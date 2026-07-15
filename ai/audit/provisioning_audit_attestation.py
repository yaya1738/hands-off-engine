from typing import Any, Dict


class ProvisioningAuditAttestation:
    def create(
        self,
        governance: Dict[str, Any],
        auditor: str = "system",
    ) -> Dict[str, Any]:
        return {
            "attestation_type": "provisioning_audit",
            "status": governance.get("status", "UNKNOWN"),
            "governance": governance,
            "auditor": auditor,
            "attested": True,
        }
