"""Read-only compatibility facade for legacy completion-flow verification.

The historical helper executed the construction controller directly. Privileged
orchestration now belongs to FactoryAuthorityGateway.
"""

import json
from datetime import datetime, timezone


def run_controller():
    """Fail closed; legacy direct controller execution is disabled."""
    return {
        "disabled": True,
        "error": "[FACTORY-AUTHORITY] legacy controller execution is disabled; submit through FactoryAuthorityGateway",
    }


def inspect_state(data):
    text = json.dumps(data).lower()
    return {
        "ready_for_review_found": "ready_for_review" in text,
        "validation_found": "validation" in text,
        "registration_found": "register" in text,
        "completion_found": "complete" in text,
    }


def run():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_completion_flow_verifier",
        "state": {},
        "decision": {
            "decision": "factory_authority_required",
            "action": "submit_completion_verification_request",
            "disabled": True,
            "next_step": "FactoryAuthorityGateway",
        },
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
