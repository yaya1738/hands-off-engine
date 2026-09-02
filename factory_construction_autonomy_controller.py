"""Read-only construction autonomy controller compatibility facade."""
import json
from datetime import datetime, timezone

TARGET = "create factory construction lifecycle controller"


def run_router(goal):
    return {
        "goal": goal,
        "authority_required": True,
        "disabled": True,
        "error": "[FACTORY-AUTHORITY] router execution is disabled; submit through FactoryAuthorityGateway",
    }


def analyze(result):
    return {
        "decision": "authority_required",
        "action": "submit_construction_request_through_FactoryAuthorityGateway",
    }


def run():
    router_result = run_router(TARGET)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_construction_autonomy_controller",
        "router_result": router_result,
        "decision": analyze(router_result),
        "disabled": True,
        "authority": "FactoryAuthorityGateway",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
