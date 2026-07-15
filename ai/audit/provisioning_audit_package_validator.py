from typing import Any, Dict, List


class ProvisioningAuditPackageValidator:
    def validate(
        self,
        package: Dict[str, Any],
    ) -> Dict[str, Any]:
        required = [
            "evidence",
            "report",
            "snapshot",
            "controls",
            "governance",
            "attestation",
        ]

        missing: List[str] = [
            key
            for key in required
            if key not in package
        ]

        return {
            "valid": len(missing) == 0,
            "missing": missing,
        }
