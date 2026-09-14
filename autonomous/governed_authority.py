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


def authorize(command: Dict[str, Any]) -> AuthorityDecision:
    """Return a fail-closed decision for a queued command.

    No command becomes executable merely by entering the queue.  LIVE work
    always requires an explicit approval state; unknown or malformed commands
    are rejected rather than inferred.
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
        return AuthorityDecision(
            command_id,
            "approved",
            "explicit approval present; downstream executor remains responsible for safety checks",
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
