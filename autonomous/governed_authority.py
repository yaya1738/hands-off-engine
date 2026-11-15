#!/usr/bin/env python3
"""Fail-closed authority seam for autonomous coordination and execution."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict
import json

from scripts.command_approval import command_fingerprint

APPROVAL_TTL = timedelta(hours=24)


@dataclass(frozen=True)
class AuthorityDecision:
    command_id: str
    decision: str
    reason: str
    execution_enabled: bool = False
    approval_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _verify_durable_approval(command: Dict[str, Any], approval_file=None):
    """Verify the independent approval record and exact approved command snapshot."""
    if approval_file is None:
        approval_file = Path(__file__).resolve().parents[1] / "state" / "approval_queue.json"
    path = Path(approval_file)
    if not path.is_file():
        return False, "durable approval record unavailable"
    try:
        queue = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(queue, dict):
            return False, "approval queue malformed"
        matches = [
            item for item in queue.get("approved", [])
            if isinstance(item, dict) and item.get("id") == command.get("id")
        ]
        if len(matches) != 1:
            return False, "approval record missing or ambiguous"
        record = matches[0]
        fingerprint = command_fingerprint(command)
        if not fingerprint or fingerprint != command.get("approval_fingerprint") or fingerprint != record.get("fingerprint"):
            return False, "approved command snapshot mismatch"
        approved_at = datetime.fromisoformat(str(record.get("approved_at", "")).replace("Z", "+00:00"))
        if approved_at.tzinfo is None:
            return False, "approval timestamp has no timezone"
        age = datetime.now(timezone.utc) - approved_at.astimezone(timezone.utc)
        if age < timedelta(0) or age > APPROVAL_TTL:
            return False, "approval expired or timestamp is in the future"
        return True, "durable approval verified"
    except (OSError, ValueError, TypeError, AttributeError):
        return False, "approval record unreadable or malformed"


def authorize(
    command: Dict[str, Any],
    *,
    execution_gate: bool | None = None,
    approval_file=None,
) -> AuthorityDecision:
    """Classify work; LIVE approval requires a durable, exact, unexpired record.

    The executor gate is additional defense in depth. This authority module
    never itself grants execution rights.
    """
    if not isinstance(command, dict):
        return AuthorityDecision("", "rejected", "command must be a dict")
    command_id = str(command.get("id") or command.get("command_id") or "")
    if not command_id:
        return AuthorityDecision("", "rejected", "missing command id")

    mode = str(command.get("mode", "DRYRUN")).upper()
    if mode not in {"DRYRUN", "LIVE"}:
        return AuthorityDecision(command_id, "rejected", "unsupported execution mode")

    if mode == "LIVE":
        if command.get("approval_status") != "approved":
            return AuthorityDecision(command_id, "approval_required", "LIVE execution requires explicit approval")
        verified, reason = _verify_durable_approval(command, approval_file)
        if not verified:
            return AuthorityDecision(command_id, "approval_required", reason)
        gate_active = execution_gate is True
        return AuthorityDecision(
            command_id,
            "approved",
            "LIVE durable approval verified; executor gate active" if gate_active
            else "LIVE durable approval verified; executor gate absent",
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
