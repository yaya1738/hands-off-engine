"""Read-only phase transition gate.

Legacy git inspection/execution is intentionally disabled. Operational
inspection must be performed by FactoryAuthorityGateway.
"""

import json
import sys


CURRENT_MILESTONE = "factory-runtime-reporting-restored-20260717"
NEXT_PHASE = "preflight_runtime_integration"
ALLOWED_NEXT_PHASE_PREFIXES = [
    "factory_autonomy_preflight",
    "factory_capability_",
    "factory_execution_",
    "factory_reporting_",
    "factory_validation_",
]


def run(cmd):
    """Compatibility boundary: never execute an external command."""
    return "[FACTORY-AUTHORITY] Legacy phase-gate command execution is disabled; use FactoryAuthorityGateway."


def main():
    result = {
        "current_milestone": CURRENT_MILESTONE,
        "next_phase": NEXT_PHASE,
        "checks": {
            "milestone_commit": {
                "passed": False,
                "found": "AUTHORITY_REQUIRED",
            },
            "workspace_separation": {
                "passed": False,
                "unexpected_files": [],
            },
        },
        "ready": False,
        "action": "submit inspection through FactoryAuthorityGateway",
        "authority": "FactoryAuthorityGateway",
    }
    print(json.dumps(result, indent=2))
    return 1


if __name__ == "__main__":
    sys.exit(main())
