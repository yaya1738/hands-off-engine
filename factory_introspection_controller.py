"""Read-only compatibility facade for legacy factory introspection control.

The historical helper launched the forensic engine directly. Privileged
orchestration is now owned by FactoryAuthorityGateway.
"""

import json
from datetime import datetime, timezone


KEYWORDS = ["inspect", "introspect", "contract", "probe", "reflection"]

MISSING_UTILITY = {
    "name": "factory_introspection_probe.py",
    "responsibility": ["discover modules", "discover classes", "discover functions", "inspect signatures", "return JSON contracts"],
}


def run_forensic_engine():
    return {
        "disabled": True,
        "error": "[FACTORY-AUTHORITY] legacy forensic execution is disabled; submit through FactoryAuthorityGateway",
    }


def find_existing_capability(report):
    matches = []
    for tool in report.get("available_tools", []):
        combined = tool.get("tool", "").lower() + " " + " ".join(tool.get("exports", [])).lower()
        found = [k for k in KEYWORDS if k in combined]
        if found:
            matches.append({"tool": tool.get("tool"), "matches": found})
    return matches


def connect_existing(matches):
    return {"action": "connect_existing_tool", "tools": matches}


def create_missing():
    return {"action": "create_missing_utility", "utility": MISSING_UTILITY}


def run():
    report = run_forensic_engine()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "controller": "factory_introspection_controller",
        "decision": {
            "decision": "factory_authority_required",
            "action": "submit_introspection_request",
            "disabled": True,
            "next_step": "FactoryAuthorityGateway",
            "legacy_report": report,
        },
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
