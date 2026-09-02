"""Read-only compatibility facade for lifecycle authority discovery.

The legacy implementation spawned the forensic engine directly. Operational
execution now belongs behind FactoryAuthorityGateway.
"""
import json
from datetime import datetime, timezone

KEYWORDS = [
    "controller", "gateway", "service", "request", "lifecycle", "workflow", "manager"
]


def run():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_lifecycle_authority_probe",
        "matches": [],
        "disabled": True,
        "authority_required": True,
        "next_step": "FactoryAuthorityGateway",
        "error": "[FACTORY-AUTHORITY] legacy forensic execution is disabled; submit through FactoryAuthorityGateway",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
