from typing import Any, Dict


class ProvisioningAuditPackage:
    def build(
        self,
        evidence: Dict[str, Any],
        report: Dict[str, Any],
        snapshot: Dict[str, Any],
        controls: Dict[str, Any],
        governance: Dict[str, Any],
        attestation: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "package_type": "provisioning_audit",
            "evidence": evidence,
            "report": report,
            "snapshot": snapshot,
            "controls": controls,
            "governance": governance,
            "attestation": attestation,
        }
