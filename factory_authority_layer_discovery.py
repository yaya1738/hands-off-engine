"""Read-only authority-layer discovery facade.

Legacy forensic-engine subprocess execution is disabled. Discovery that needs
execution must be submitted through FactoryAuthorityGateway.
"""
import json
from datetime import datetime, timezone

TARGETS = {
    "capability_router": ["capability", "router", "routing"],
    "decision_engine": ["decision", "engine"],
    "build_controller": ["controller", "builder", "constructor"],
    "improvement_planner": ["improvement", "planner"],
    "runtime_coordinator": ["runtime", "coordinator"],
}


def run_forensic_engine():
    return {"disabled": True, "authority": "FactoryAuthorityGateway"}


def discover():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_authority_layer_discovery",
        "decisions": {},
        "decision": "authority_required",
        "authority": "FactoryAuthorityGateway",
        "disabled": True,
    }


if __name__ == "__main__":
    print(json.dumps(discover(), indent=2))
