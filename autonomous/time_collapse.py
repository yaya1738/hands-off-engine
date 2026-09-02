"""Read-only compatibility facade for the legacy time-collapse engine.

Trading, process execution, remote access, notifications, and state mutation
require FactoryAuthorityGateway and are intentionally fail-closed here.
"""
import json
from datetime import datetime, timezone


def log(msg: str):
    print(f"[TIME-COLLAPSE] {msg}")


def send_telegram(message: str):
    log("[FACTORY-AUTHORITY] notification delivery is disabled")
    return False


def _disabled(vector):
    return {"vector": vector, "results": [], "authority_required": True,
            "disabled": True}


def accelerate_capital_awareness(): return _disabled("capital_awareness")
def accelerate_income_channels(): return _disabled("income_channels")
def accelerate_automation(): return _disabled("automation")
def accelerate_intelligence(): return _disabled("intelligence")
def accelerate_momentum(): return _disabled("momentum")


def define_completed_state():
    return {"trading_enabled": False, "human_intervention_needed": True,
            "authority": "FactoryAuthorityGateway"}


def calculate_gap(current: dict, target: dict) -> dict:
    return {"authority_required": True}


def collapse_timeline():
    return {"timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": "authority_required",
            "authority": "FactoryAuthorityGateway", "disabled": True}


def execute_immediate_actions():
    return ["[FACTORY-AUTHORITY] immediate execution is disabled; submit through FactoryAuthorityGateway"]


if __name__ == "__main__":
    print(json.dumps(collapse_timeline(), indent=2))
