"""Outbound Telegram notifications for autonomous task completion.

The autonomous executor can communicate meaningful outcomes directly to the
authenticated external control surface; a consumer chat session is not needed.
"""

from __future__ import annotations

import json
import os
from typing import Any


def notify_task_result(task: dict[str, Any], result: dict[str, Any]) -> bool:
    chat_id = str(task.get("metadata", {}).get("chat_id", "")).strip()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not chat_id or not token:
        return False

    execution = result.get("execution", {}) if isinstance(result, dict) else {}
    success = execution.get("success")
    steps = execution.get("steps_completed", [])
    summary = (
        f"Autonomous task update\n\n"
        f"Task: {task.get('title', 'request')}\n"
        f"Result: {'completed' if success is True else 'execution attempted'}\n"
        f"Steps: {', '.join(map(str, steps)) if steps else 'recorded in system evidence'}"
    )

    try:
        import requests
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": summary},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception:
        return False
