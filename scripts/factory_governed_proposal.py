#!/usr/bin/env python3
"""Translate reasoning evidence into a bounded proposal for governance.

A proposal is an intent artifact, not an authorization. This helper never
executes, approves, routes, or enables work.
"""
from __future__ import annotations

from typing import Any, Dict


def build_governed_proposal(reasoning: Dict[str, Any]) -> Dict[str, Any]:
    """Build a fail-closed proposal from an existing reasoning context."""
    if not isinstance(reasoning, dict) or not reasoning.get("available", False):
        return {"available": False}

    diagnosis = reasoning.get("diagnosis")
    if not isinstance(diagnosis, str) or not diagnosis:
        return {"available": False}

    assessment = reasoning.get("assessment")
    if not isinstance(assessment, dict):
        assessment = {}
    objective = assessment.get("objective")
    if objective is not None and not isinstance(objective, str):
        objective = None

    return {
        "available": True,
        "proposal": {
            "kind": "factory_improvement_proposal",
            "diagnosis": diagnosis,
            "objective": objective,
            "observation_complete": bool(reasoning.get("observation_complete", False)),
            "requires_governance": True,
            "execution_enabled": False,
        },
    }


__all__ = ["build_governed_proposal"]
