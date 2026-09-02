"""Verification-only phase transition compatibility gate.

Repository inspection and mutation are operational authorities. This legacy
helper no longer shells out to git and cannot advance phases itself.
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
    return "[FACTORY-AUTHORITY] legacy command execution disabled"


def main():
    result = {
        "current_milestone": CURRENT_MILESTONE,
        "next_phase": NEXT_PHASE,
        "checks": {},
        "ready": False,
        "action": "submit repository verification through FactoryAuthorityGateway",
        "authority": "FactoryAuthorityGateway",
    }
    print(json.dumps(result, indent=2))
    sys.exit(1)


if __name__ == "__main__":
    main()
