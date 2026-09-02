"""Read-only completion authority discovery compatibility facade."""
import json
from datetime import datetime, timezone

KEYWORDS = ["approve", "finalize", "complete", "commit", "promote", "publish", "register", "verify"]


def run_probe():
    return {"disabled": True, "authority": "FactoryAuthorityGateway"}


def search(data):
    text = json.dumps(data).lower()
    matches = [word for word in KEYWORDS if word in text]
    return {
        "decision": "authority_required",
        "matches": matches,
        "action": "submit_discovery_request_through_FactoryAuthorityGateway",
    }


def run():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_completion_authority_discovery",
        "decision": search(run_probe()),
        "disabled": True,
        "authority": "FactoryAuthorityGateway",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
