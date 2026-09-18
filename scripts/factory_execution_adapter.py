#!/usr/bin/env python3
"""Fail-closed bridge from governed commands to the Factory authority gateway.

This adapter is the only intended bridge from the Sep-18 control plane into the
Factory execution surface.  It never treats a task payload as execution
authority: LIVE execution requires explicit approval plus this adapter's
trusted executor opt-in.

If the Factory runtime is unavailable, the adapter returns a bounded blocked
result instead of falling back to legacy execution.
"""

from __future__ import annotations

from typing import Any, Dict

from autonomous.governed_authority import authorize


def execute_factory_command(
    command: Dict[str, Any],
    *,
    execution_gate: bool = False,
) -> Dict[str, Any]:
    """Execute one explicitly approved Factory objective, fail closed."""
    if not isinstance(command, dict):
        return {"status": "rejected", "reason": "command must be a dict"}

    decision = authorize(command, execution_gate=execution_gate)

    if decision.decision != "approved":
        return {
            "status": decision.decision,
            "reason": decision.reason,
            "command_id": decision.command_id,
        }

    if not execution_gate:
        return {
            "status": "awaiting_executor_gate",
            "reason": decision.reason,
            "command_id": decision.command_id,
        }

    objective = command.get("objective")
    if objective is None:
        payload = command.get("payload") or {}
        objective = payload.get("objective") or payload.get("action")

    if not isinstance(objective, str) or not objective.strip():
        return {
            "status": "rejected",
            "reason": "missing Factory objective",
            "command_id": decision.command_id,
        }

    try:
        from ai.factory.authority_gateway import FactoryAuthorityGateway
    except ImportError as exc:
        return {
            "status": "blocked",
            "reason": "Factory authority gateway unavailable",
            "command_id": decision.command_id,
            "error": str(exc),
        }

    try:
        gateway = FactoryAuthorityGateway()
        result = gateway.execute_autonomous(
            objective.strip(),
            idempotency_key=decision.command_id,
        )
        return {
            "status": "completed",
            "command_id": decision.command_id,
            "factory": result,
        }
    except Exception as exc:
        return {
            "status": "error",
            "command_id": decision.command_id,
            "error": str(exc),
        }


__all__ = ["execute_factory_command"]
