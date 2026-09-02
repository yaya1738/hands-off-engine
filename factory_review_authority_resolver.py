"""Read-only compatibility facade for review-authority discovery.

The legacy implementation spawned another controller directly. Operational
execution now belongs behind FactoryAuthorityGateway.
"""
import json
from datetime import datetime, timezone

KEYWORDS = ["review", "approve", "validate", "verification", "complete", "accept"]


def probe():
    return {
        "disabled": True,
        "authority_required": True,
        "next_step": "FactoryAuthorityGateway",
        "error": "[FACTORY-AUTHORITY] legacy controller execution is disabled; submit through FactoryAuthorityGateway",
    }


def find(data):
    text = json.dumps(data).lower()
    return [word for word in KEYWORDS if word in text]


def run():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_review_authority_resolver",
        "decision": {
            "decision": "factory_authority_required",
            "matches": find(probe()),
            "action": "submit_review_authority_request",
        },
        "disabled": True,
        "next_step": "FactoryAuthorityGateway",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
