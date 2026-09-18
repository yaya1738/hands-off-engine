#!/usr/bin/env python3
"""Build a bounded reasoning input from shared Factory observations.

This is deliberately below planning and authority: it describes evidence for a
reasoner but never selects work, authorizes commands, or enables execution.
"""
from __future__ import annotations

from typing import Any, Dict

from scripts.factory_context_diagnosis import diagnose_factory_context


def build_factory_reasoning_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Return bounded evidence plus diagnosis for a downstream reasoner."""
    if not isinstance(context, dict):
        return {"available": False}

    diagnosis = diagnose_factory_context(context)
    if not diagnosis.get("available", False):
        return {"available": False}

    authority = context.get("authority")
    if not isinstance(authority, dict):
        authority = {"available": False}

    # Reasoning may observe authority classification, but execution capability
    # is never part of the reasoning contract.
    authority_observation = {
        "available": bool(authority.get("available", False)),
        "msg_id": authority.get("msg_id"),
        "reply_to": authority.get("reply_to"),
        "task_id": authority.get("task_id"),
        "decision": authority.get("decision"),
        "reason": authority.get("reason"),
        "approval_required": bool(authority.get("approval_required", True)),
        "decided_at": authority.get("decided_at"),
    }

    def _mapping(name: str) -> Dict[str, Any]:
        value = context.get(name)
        return dict(value) if isinstance(value, dict) else {"available": False}

    return {
        "available": True,
        "diagnosis": diagnosis["diagnosis"],
        "observation_complete": diagnosis["observation_complete"],
        "interaction": _mapping("interaction"),
        "system_health": _mapping("system_health"),
        "admission": _mapping("admission"),
        "authority": authority_observation,
        "assessment": _mapping("assessment"),
    }


__all__ = ["build_factory_reasoning_context"]
