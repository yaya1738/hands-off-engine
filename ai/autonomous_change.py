#!/usr/bin/env python3
"""Compatibility proposal API with a fail-closed execution boundary."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.approval_queue import ApprovalQueue, send_approval_notification


def propose_change(title: str, description: str, change_type: str,
                   files: list, action: dict, risk_level: str = "medium") -> dict:
    """Record a proposal without executing caller-supplied actions."""
    queue = ApprovalQueue()
    change_id = queue.add_change(
        title=title,
        description=description,
        change_type=change_type,
        files_affected=files,
        proposed_action=action,
        risk_level=risk_level,
    )
    change = queue.get_change(change_id)
    send_approval_notification(change_id, change)
    return {
        "applied": False,
        "change_id": change_id,
        "status": "pending_governed_execution",
        "execution_authority": "factory_authority_gateway",
        "message": f"Change recorded: {change_id}. No legacy auto-execution is permitted.",
    }
