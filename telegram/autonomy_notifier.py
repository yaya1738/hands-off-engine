"""Outbound notifications for autonomous task completion.

Notification is deliberately best-effort: execution success and authority state
must never depend on an external notification provider being available.
"""

from __future__ import annotations

from typing import Any


def notify_task_result(task: dict[str, Any], result: dict[str, Any]) -> bool:
    """Notify the requester through the durable messaging failover stack."""
    execution = result.get("execution", {}) if isinstance(result, dict) else {}
    success = execution.get("success")
    steps = execution.get("steps_completed", [])
    summary = (
        "Autonomous task update\n\n"
        f"Task: {task.get('title', 'request')}\n"
        f"Result: {'completed' if success is True else 'execution attempted'}\n"
        f"Steps: {', '.join(map(str, steps)) if steps else 'recorded in system evidence'}"
    )

    try:
        from autonomous.messaging_bridge import MessagingBridge

        # Normal-priority routing uses the configured Telegram/SMS/WhatsApp
        # failover chain. The bridge itself remains best-effort and returns
        # False when no configured transport can deliver the message.
        return bool(MessagingBridge().notify(summary, priority="normal", channel="all"))
    except Exception:
        return False
