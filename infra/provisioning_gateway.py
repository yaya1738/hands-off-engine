#!/usr/bin/env python3
"""
Provisioning Gateway
Central audit-only authority layer.

No infrastructure mutations are executed.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from ai.audit.provisioning_provenance import create_provenance


AUDIT_FILE = Path("state/audit/provisioning_events.jsonl")


def audit_event(event):
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with AUDIT_FILE.open("a") as f:
        f.write(json.dumps(event) + "\n")


def request_provision(
    requester,
    action,
    cost_usd=None,
    capital_context=None,
):
    provenance = create_provenance(
        requester=requester,
        intent=action,
        estimated_cost_usd=cost_usd,
        capital_context=capital_context,
    )

    event = {
        **provenance,
        "event": "provisioning_request",
        "action": action,
        "cost_usd": cost_usd,
        "decision": "AUDIT_ONLY",
    }

    audit_event(event)

    return event


if __name__ == "__main__":
    print(
        request_provision(
            "test",
            "create_droplet",
            0,
            {"capital_available_usd": 0},
        )
    )
