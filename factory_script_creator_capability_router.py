"""Read-only script-creator capability router.

Legacy analyzer execution is disabled; construction authority belongs to
FactoryAuthorityGateway.
"""

import json
from datetime import datetime, timezone


CREATION_KEYWORDS = [
    "create", "build", "develop", "artifact", "generate", "constructor", "write",
]

NEW_COMPONENT = {
    "name": "Factory Script Creator",
    "responsibility": ["generate file", "run syntax check", "run tests", "register artifact"],
    "scope": "narrow construction capability",
}


def run_capability_analyzer():
    return {
        "authority_required": True,
        "message": "[FACTORY-AUTHORITY] Legacy capability analyzer execution is disabled; use FactoryAuthorityGateway.",
        "capabilities": {},
    }


def find_construction_capability(report):
    text = json.dumps(report).lower()
    return [keyword for keyword in CREATION_KEYWORDS if keyword in text]


def create_missing_creator():
    return {"decision": "create_missing_capability", "capability": NEW_COMPONENT, "status": "planned"}


def run():
    report = run_capability_analyzer()
    matches = find_construction_capability(report)
    decision = {
        "decision": "authority_required",
        "matches": matches,
        "source": "FactoryAuthorityGateway",
    }
    if not matches:
        decision["fallback"] = create_missing_creator()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_script_creator_capability_router",
        "decision": decision,
        "authority_required": True,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
