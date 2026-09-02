"""Compatibility facade for legacy capability-construction automation.

The historical implementation executed a sequence of local Python tools and
persisted a report directly. That made this helper an autonomous execution
boundary outside FactoryAuthorityGateway. Privileged construction and state
mutation now belong to the Factory authority layer.
"""

import json
import sys
from datetime import datetime, timezone


TOOLS = (
    "factory_forensic_engine.py",
    "factory_artifact_registry.py",
    "factory_capability_analyzer.py",
    "factory_architecture_audit.py",
    "factory_capability_decision_engine.py",
    "factory_capability_integration_planner.py",
    "factory_capability_safety_gate.py",
)


def run_tool(tool):
    """Fail closed; legacy direct tool execution is no longer permitted."""
    return {
        "tool": tool,
        "success": False,
        "error": "[FACTORY-AUTHORITY] legacy tool execution is disabled; submit through FactoryAuthorityGateway",
    }


def build_capability(goal):
    """Return a non-mutating compatibility result without executing tools."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal,
        "mode": "factory_authority_required",
        "tools": [],
        "decision": {
            "action": "submit_capability_construction_request",
            "next_step": "FactoryAuthorityGateway",
            "disabled": True,
        },
    }


def main():
    goal = " ".join(sys.argv[1:]) or "unknown capability"
    print(json.dumps(build_capability(goal), indent=2))


if __name__ == "__main__":
    main()
