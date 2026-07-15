from typing import Any, Dict, List


class ProvisioningPolicyDriftDetector:
    def compare(self, records: List[Any]) -> Dict[str, Any]:
        versions = sorted(
            {
                getattr(record, "policy_version", None)
                for record in records
                if getattr(record, "policy_version", None) is not None
            }
        )

        affected_records = [
            getattr(record, "request_id", None)
            for record in records
            if getattr(record, "policy_version", None) is not None
        ]

        return {
            "drift_detected": len(versions) > 1,
            "policy_versions": versions,
            "affected_records": affected_records,
            "issues": (
                ["multiple_policy_versions_detected"]
                if len(versions) > 1
                else []
            ),
        }
