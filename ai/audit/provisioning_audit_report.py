from typing import Any, Dict


class ProvisioningAuditReport:
    def generate(
        self,
        summary: Dict[str, Any],
        evidence: Dict[str, Any],
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        metadata = metadata or {}

        status = "PASS"

        if not evidence.get("complete", False):
            status = "FAIL"

        if summary.get("issues"):
            status = "FAIL"

        return {
            "report_type": "provisioning_audit",
            "status": status,
            "summary": summary,
            "evidence": evidence,
            "metadata": metadata,
        }
