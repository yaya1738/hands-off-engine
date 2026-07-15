from typing import Any, Dict


class ProvisioningEvidenceCollector:
    def collect(
        self,
        provenance: Any = None,
        decision: Any = None,
        policy: Any = None,
        integrity: Any = None,
        timeline: Any = None,
    ) -> Dict[str, Any]:
        artifacts = {
            "provenance": provenance,
            "decision": decision,
            "policy": policy,
            "integrity": integrity,
            "timeline": timeline,
        }

        missing = [
            name
            for name, value in artifacts.items()
            if value is None
        ]

        return {
            "evidence_id": "provisioning-evidence",
            "artifacts": artifacts,
            "complete": len(missing) == 0,
            "missing": missing,
        }
