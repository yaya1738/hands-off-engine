from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict
import json


@dataclass
class PolicyRecord:
    policy_id: str
    version: str
    policy_hash: str
    rules: Dict[str, Any]


class ProvisioningPolicyRegistry:
    def register(
        self,
        policy_id: str,
        version: str,
        rules: Dict[str, Any],
    ) -> PolicyRecord:
        payload = json.dumps(
            rules,
            sort_keys=True,
        ).encode()

        policy_hash = sha256(payload).hexdigest()

        return PolicyRecord(
            policy_id=policy_id,
            version=version,
            policy_hash=policy_hash,
            rules=rules,
        )
