"""Read-only introspection capability router.

Legacy forensic-engine execution is disabled; privileged inspection must be
routed through FactoryAuthorityGateway.
"""

import json
from datetime import datetime, timezone


KEYWORDS = ["inspect", "introspect", "contract", "probe", "reflection"]


def run_forensic_engine():
    return {
        "authority_required": True,
        "message": "[FACTORY-AUTHORITY] Legacy forensic engine execution is disabled; use FactoryAuthorityGateway.",
        "available_tools": [],
    }


def find_existing_probe_tools(report):
    matches = []
    for tool in report.get("available_tools", []):
        name = tool.get("tool", "").lower()
        exports = " ".join(tool.get("exports", [])).lower()
        combined = name + " " + exports
        found = [keyword for keyword in KEYWORDS if keyword in combined]
        if found:
            matches.append({"tool": tool.get("tool"), "matches": found, "exports": tool.get("exports", [])})
    return matches


def run():
    report = run_forensic_engine()
    existing = find_existing_probe_tools(report)
    decision = {
        "decision": "authority_required",
        "tools": existing,
        "authority": "FactoryAuthorityGateway",
    }
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_introspection_capability_router",
        "decision": decision,
        "authority_required": True,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
