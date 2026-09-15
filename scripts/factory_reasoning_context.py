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

    return {
        "available": True,
        "diagnosis": diagnosis["diagnosis"],
        "observation_complete": diagnosis["observation_complete"],
        "interaction": dict(context.get("interaction", {})),
        "system_health": dict(context.get("system_health", {})),
        "admission": dict(context.get("admission", {})),
        "authority": dict(context.get("authority", {})),
        "assessment": dict(context.get("assessment", {})),
    }


__all__ = ["build_factory_reasoning_context"]
