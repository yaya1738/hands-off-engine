#!/usr/bin/env python3
"""Build a bounded handoff from a proposal into the existing governance seam.

This adapter creates no authorization and performs no execution. It only
preserves proposal identity so the established authority boundary can evaluate
it later.
"""
from __future__ import annotations

from typing import Any, Dict


def build_governed_handoff(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """Return a correlation-preserving handoff request, fail-closed."""
    if not isinstance(proposal, dict) or not proposal.get("available", False):
        return {"available": False}

    body = proposal.get("proposal")
    if not isinstance(body, dict) or not body.get("requires_governance", False):
        return {"available": False}

    return {
        "available": True,
        "handoff": {
            "kind": "factory_governed_handoff",
            "proposal_kind": body.get("kind"),
            "diagnosis": body.get("diagnosis"),
            "objective": body.get("objective"),
            "observation_complete": bool(body.get("observation_complete", False)),
            "requires_governance": True,
            "execution_enabled": False,
        },
    }


__all__ = ["build_governed_handoff"]
