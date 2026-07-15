from typing import Any, Dict, List


class ProvisioningAuditArchiveIndex:
    def __init__(self):
        self._packages: List[Dict[str, Any]] = []

    def add(self, package_metadata: Dict[str, Any]) -> None:
        self._packages.append(package_metadata)

    def find_by_id(self, package_id: str) -> List[Dict[str, Any]]:
        return [
            package
            for package in self._packages
            if package.get("package_id") == package_id
        ]

    def find_by_hash(self, package_hash: str) -> List[Dict[str, Any]]:
        return [
            package
            for package in self._packages
            if package.get("hash") == package_hash
        ]

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        return [
            package
            for package in self._packages
            if package.get("status") == status
        ]
