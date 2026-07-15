from typing import Any, Dict, List


class ProvisioningAuditPackageCompare:
    def compare(
        self,
        old_package: Dict[str, Any],
        new_package: Dict[str, Any],
    ) -> Dict[str, Any]:
        differences: List[Dict[str, Any]] = []

        keys = set(old_package.keys()) | set(new_package.keys())

        for key in sorted(keys):
            old_value = old_package.get(key)
            new_value = new_package.get(key)

            if old_value != new_value:
                differences.append(
                    {
                        "section": key,
                        "old": old_value,
                        "new": new_value,
                    }
                )

        return {
            "changed": len(differences) > 0,
            "differences": differences,
        }
