from typing import Any, Dict, List


class ProvisioningAuditPolicy:
    def evaluate(
        self,
        evidence: Dict[str, Any],
        integrity: Any,
        consistency: Any,
    ) -> Dict[str, Any]:
        findings: List[str] = []

        if not evidence.get("complete", False):
            findings.append("incomplete_evidence")

        if not getattr(integrity, "valid", False):
            findings.append("integrity_failure")

        if not getattr(consistency, "valid", False):
            findings.append("consistency_failure")

        return {
            "compliant": len(findings) == 0,
            "findings": findings,
        }
