#!/usr/bin/env python3
"""
Autonomous Change Helper

Provides simple API for autonomous agents to propose changes
that either auto-apply or require approval based on risk level.

Usage from autonomous agents:
    from ai.autonomous_change import propose_change

    propose_change(
        title="Increase risk limit",
        description="Alpha signals showing consistent edge >8%, safe to increase limit",
        change_type="trading_parameters",
        files=["config/risk_limits.json"],
        action={
            "type": "edit_file",
            "file_path": "/root/hands-off-engine/config/risk_limits.json",
            "old_content": '"max_position": 100',
            "new_content": '"max_position": 200'
        },
        risk_level="high"
    )
"""

from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.approval_queue import ApprovalQueue, needs_approval, send_approval_notification


def propose_change(
    title: str,
    description: str,
    change_type: str,
    files: list,
    action: dict,
    risk_level: str = "medium"
) -> dict:
    """
    Propose a change - either auto-applies or queues for approval.

    Args:
        title: Short title of change
        description: Detailed description
        change_type: Type (config, code, parameters, etc)
        files: List of files affected
        action: Dict with action details (type, file_path, etc)
        risk_level: low, medium, high

    Returns:
        dict with:
            - applied: bool (True if auto-applied, False if queued)
            - change_id: str (if queued for approval)
            - result: dict (if auto-applied)
    """
    queue = ApprovalQueue()

    # Determine if approval needed
    if needs_approval(change_type, files) or risk_level == "high":
        # Queue for approval
        change_id = queue.add_change(
            title=title,
            description=description,
            change_type=change_type,
            files_affected=files,
            proposed_action=action,
            risk_level=risk_level
        )

        # Send Telegram notification
        change = queue.get_change(change_id)
        send_approval_notification(change_id, change)

        return {
            "applied": False,
            "change_id": change_id,
            "status": "pending_approval",
            "message": f"Change queued for approval: {change_id}"
        }

    else:
        # Safe to auto-apply
        # Create temporary queue entry
        change_id = queue.add_change(
            title=title,
            description=description,
            change_type=change_type,
            files_affected=files,
            proposed_action=action,
            risk_level=risk_level
        )

        # Auto-approve
        queue.approve(change_id)

        # Execute
        result = queue.execute_approved(change_id)

        return {
            "applied": True,
            "change_id": change_id,
            "status": "auto_applied",
            "result": result
        }


# Example usage
if __name__ == "__main__":
    # Example 1: High-risk change requiring approval
    result = propose_change(
        title="Increase max position size to $200",
        description="Alpha signals consistently showing 8%+ edge. Safe to increase position limits.",
        change_type="trading_parameters",
        files=["config/risk_limits.json"],
        action={
            "type": "edit_file",
            "file_path": "/root/hands-off-engine/config/risk_limits.json",
            "old_content": '"max_position": 100',
            "new_content": '"max_position": 200'
        },
        risk_level="high"
    )

    print(f"Result: {result}")

    if not result["applied"]:
        print(f"\nChange {result['change_id']} is pending your approval via Telegram")
        print(f"Send: /approve {result['change_id']}")
