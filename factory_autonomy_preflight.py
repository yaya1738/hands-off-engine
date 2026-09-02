"""Read-only compatibility facade for legacy autonomy preflight orchestration.

The historical helper executed local Python stages and wrote a report directly.
Privileged orchestration and persistence are now owned by FactoryAuthorityGateway.
"""

import json
import sys
from datetime import datetime, timezone


STAGES = (
    "factory_capability_scanner.py",
    "factory_capability_analyzer.py",
    "factory_capability_decision_engine.py",
    "factory_capability_integration_planner.py",
    "factory_capability_safety_gate.py",
    "factory_capability_execution_adapter.py",
    "factory_execution_integration_discovery.py",
    "factory_execution_binding_planner.py",
    "factory_validation_resolver.py",
)

REPORT_FILES = (
    "factory_capability_report.json",
    "factory_capability_analysis.json",
    "factory_capability_decisions.json",
    "factory_capability_integration_plan.json",
    "factory_capability_execution_request.json",
    "factory_capability_execution_plan.json",
    "factory_execution_integration_discovery.json",
    "factory_execution_binding_plan.json",
    "factory_validation_plan.json",
)


def run_stage(stage):
    """Fail closed; legacy direct stage execution is disabled."""
    return {
        "stage": stage,
        "return_code": None,
        "disabled": True,
        "error": "[FACTORY-AUTHORITY] legacy stage execution is disabled; submit through FactoryAuthorityGateway",
    }


def load_outputs():
    """Return an empty compatibility result; legacy report reads are not authoritative."""
    return {}


def main():
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stages": [],
        "outputs": {},
        "decision": {
            "action": "submit_autonomy_preflight_request",
            "next_step": "FactoryAuthorityGateway",
            "disabled": True,
        },
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
