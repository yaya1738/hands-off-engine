from typing import Any, Dict


class ProvisioningAuditControlMatrix:
    def build(
        self,
        integrity: Any,
        consistency: Any,
        policy: Any,
        evidence: Dict[str, Any],
    ) -> Dict[str, Any]:
        controls = {
            "integrity": getattr(integrity, "valid", False),
            "consistency": getattr(consistency, "valid", False),
            "policy": policy.get("compliant", False),
            "evidence": evidence.get("complete", False),
        }

        return {
            "controls": controls,
            "passed": all(controls.values()),
            "failed_controls": [
                name
                for name, passed in controls.items()
                if not passed
            ],
        }
