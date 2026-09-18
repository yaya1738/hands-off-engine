#!/usr/bin/env python3
"""Project authority correlation into the existing shared observation contract."""
from __future__ import annotations

from typing import Any, Dict

from scripts.factory_authority_correlation import correlate_authority_decision


def project_factory_authority_observation(
    proposal: Dict[str, Any], decision: Dict[str, Any]
) -> Dict[str, Any]:
    """Return bounded authority correlation evidence; never mutate the bus."""
    correlation = correlate_authority_decision(proposal, decision)
    if not correlation.get("available", False):
        return {"available": False}

    return {
        "available": True,
        "msg_id": correlation.get("msg_id"),
        "task_id": correlation.get("task_id"),
        "correlated": bool(correlation.get("correlated", False)),
        "msg_id_match": bool(correlation.get("msg_id_match", False)),
        "task_id_match": bool(correlation.get("task_id_match", False)),
    }


__all__ = ["project_factory_authority_observation"]
