#!/usr/bin/env python3
"""Fail-closed authority seam between autonomous coordination and execution.

This module deliberately authorizes nothing by default.  It provides a stable,
reusable contract for the governed root to classify queued work and require an
explicit approval record before any LIVE execution can be considered.
"""
from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass(frozen=True)
class AuthorityDecision:
    command_id: str
    decision: str
    reason: str
    execution_enabled: bool = False
    approval_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def authorize(command: Dict[str, Any], *, execution_gate: bool | None = None) -> AuthorityDecision:
    """Return a fail-closed decision for a queued command.

    No command becomes executable merely by entering the queue.  LIVE work
    always requires an explicit approval state; unknown or malformed commands
    are rejected rather than inferred.

    The ``execution_gate`` parameter is an additional safety control.  When
    set to ``True`` the executor explicitly opts in; when ``False`` or
    ``None`` (the default) the gate remains closed.  This ensures that
    even an approved LIVE command cannot execute unless an external gate
    is explicitly opened — a defense-in-depth measure against accidental
    or compromised approval records.

    ``execution_enabled`` is **always** ``False`` in this module.  The
    authority layer classifies work but never grants execution rights.
    """
    command_id = str(command.get("id") or command.get("command_id") or "")
    if not command_id:
        return AuthorityDecision("", "rejected", "missing command id")

    mode = str(command.get("mode", "DRYRUN")).upper()
    if mode not in {"DRYRUN", "LIVE"}:
        return AuthorityDecision(command_id, "rejected", "unsupported execution mode")

    if mode == "LIVE":
        if command.get("approval_status") != "approved":
            return AuthorityDecision(
                command_id,
                "approval_required",
                "LIVE execution requires explicit approval",
            )
        # Even with approval, execution_enabled is always False.
        # The execution_gate provides an additional opt-in layer.
        gate_active = execution_gate is True
        reason = (
            "LIVE approved; executor gate active" if gate_active
            else "LIVE approved but executor gate absent"
        )
        return AuthorityDecision(
            command_id,
            "approved",
            reason,
            execution_enabled=False,
            approval_required=True,
        )

    return AuthorityDecision(
        command_id,
        "dryrun_only",
        "DRYRUN is observable but does not grant LIVE execution authority",
        execution_enabled=False,
        approval_required=False,
    )
