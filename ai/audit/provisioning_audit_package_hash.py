import hashlib
import json
from typing import Any, Dict


class ProvisioningAuditPackageHash:
    def calculate(
        self,
        package: Dict[str, Any],
    ) -> Dict[str, str]:
        payload = json.dumps(
            package,
            sort_keys=True,
            default=str,
        ).encode()

        digest = hashlib.sha256(payload).hexdigest()

        return {
            "algorithm": "sha256",
            "hash": digest,
        }
