#!/usr/bin/env python3
"""Compatibility proposal API with a fail-closed execution boundary.

Legacy callers may still create persistent approval records, but this module
is not an execution authority. Approved work must be consumed by the governed
Factory authority path.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.approval_queue import ApprovalQueue, send_approval_notification


def propose_change(
    title: str,
    description: str,
    change_type: str,
    files: list,
    action: dict,
    risk_level: str = "medium",
) -> dict:
    """Record a proposal without executing caller-supplied actions.

    The historical implementation auto-executed low-risk actions and exposed
    a shell/file execution path through ``ApprovalQueue``. That is no longer
    permitted. Every proposal is recorded and handed to the governed authority
    path for later processing.
    """
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
        "message": (
            f"Change recorded: {change_id}. "
            "No legacy auto-execution is permitted."
        ),
    }


if __name__ == "__main__":
    print(
        propose_change(
            title="Authority boundary self-test",
            description="Verify that legacy proposals do not execute directly.",
            change_type="system_architecture",
            files=["tests/"],
            action={"type": "disabled_legacy_execution"},
            risk_level="low",
        )
    )
