from typing import Dict


class ProvisioningAuditRetention:
    def assign(
        self,
        artifact_type: str,
        retention_class: str,
    ) -> Dict[str, str]:
        return {
            "artifact_type": artifact_type,
            "retention_class": retention_class,
            "managed": True,
        }
