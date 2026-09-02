"""Read-only completion registration resolver compatibility facade."""
import json
from datetime import datetime, timezone

TARGETS = ["register", "artifact", "verification", "complete"]


def get_introspection():
    return {"disabled": True, "authority_required": True}


def resolve(data):
    text = json.dumps(data).lower()
    matches = [target for target in TARGETS if target in text]
    return {
        "decision": "authority_required",
        "action": "submit_registration_request_through_FactoryAuthorityGateway",
        "matches": matches,
    }


def run():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_completion_registration_resolver",
        "decision": resolve(get_introspection()),
        "disabled": True,
        "authority": "FactoryAuthorityGateway",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
