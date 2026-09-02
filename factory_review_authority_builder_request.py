"""Fail-closed compatibility boundary for review-authority construction requests."""

import json
from datetime import datetime, timezone


GOAL = "create factory review authority adapter"


def request():
    return {
        "authority_required": True,
        "message": "[FACTORY-AUTHORITY] Legacy construction-router execution is disabled; use FactoryAuthorityGateway.",
    }


def run():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_review_authority_builder_request",
        "goal": GOAL,
        "construction_request": request(),
        "authority": "FactoryAuthorityGateway",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
