#!/usr/bin/env python3

"""
Provisioning decision provenance records.

Metadata only.
No execution authority.
No infrastructure mutations.
"""

import uuid
from datetime import datetime, timezone


def create_provenance(
    requester,
    intent,
    estimated_cost_usd=None,
    capital_context=None,
    approval_status="AUDIT_ONLY",
    reason=None,
):
    return {
        "audit_id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "requester": requester,
        "intent": intent,
        "estimated_cost_usd": estimated_cost_usd,
        "capital_context": capital_context or {},
        "authority_owner": "ProvisioningGateway",
        "approval_status": approval_status,
        "decision_reason": reason
        or "Awaiting provisioning authority policy",
        "executor": None,
        "execution_enabled": False,
    }
