"""Read-only registration contract resolver compatibility facade."""
import json
from datetime import datetime, timezone


def probe():
    return {"contracts": [], "authority_required": True}


def resolve(data):
    contracts = data.get("contracts", []) if isinstance(data, dict) else []
    matches = []
    for item in contracts:
        name = item.get("class", "").lower()
        methods = item.get("methods", {})
        if "artifact" in name or "verification" in name or "register" in str(methods).lower():
            matches.append(item)
    return {
        "decision": "authority_required",
        "action": "submit_registration_probe_through_FactoryAuthorityGateway",
        "contracts": matches,
    }


def run():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_registration_contract_resolver",
        "decision": resolve(probe()),
        "disabled": True,
        "authority": "FactoryAuthorityGateway",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
