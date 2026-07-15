from typing import Any, Dict, List


class ProvisioningAuditSnapshotCompare:
    def compare(
        self,
        old_snapshot: Dict[str, Any],
        new_snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        differences: List[Dict[str, Any]] = []

        keys = set(old_snapshot.keys()) | set(new_snapshot.keys())

        for key in sorted(keys):
            old_value = old_snapshot.get(key)
            new_value = new_snapshot.get(key)

            if old_value != new_value:
                differences.append(
                    {
                        "field": key,
                        "old": old_value,
                        "new": new_value,
                    }
                )

        return {
            "changed": len(differences) > 0,
            "differences": differences,
        }
