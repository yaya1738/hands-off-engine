#!/usr/bin/env python3
"""
Approval Queue System

Manages changes that require user approval before execution.
Integrates with Telegram bot for notifications and approval workflow.

Auto-apply (safe):
- Logging updates, metrics, health checks
- Documentation, comments
- Non-critical bug fixes
- Performance optimizations

Require approval (risky):
- Trading parameters (limits, sizes)
- Strategy/algorithm changes
- Configuration (API keys, cron)
- Critical code paths (execution, orders)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

REPO_ROOT = Path(__file__).parent.parent
QUEUE_FILE = REPO_ROOT / "state" / "approval_queue.json"


class ApprovalQueue:
    """Manages pending changes requiring user approval."""

    def __init__(self):
        self.queue_file = QUEUE_FILE
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_queue(self) -> Dict:
        """Load approval queue from disk."""
        if not self.queue_file.exists():
            return {"pending": [], "approved": [], "rejected": []}

        with open(self.queue_file) as f:
            return json.load(f)

    def _save_queue(self, queue: Dict):
        """Save approval queue to disk."""
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f, indent=2)

    def add_change(
        self,
        title: str,
        description: str,
        change_type: str,
        files_affected: List[str],
        proposed_action: Dict,
        risk_level: str = "medium"
    ) -> str:
        """
        Add a change to the approval queue.

        Args:
            title: Short title of change
            description: Detailed description
            change_type: Type (config, code, parameters, etc)
            files_affected: List of files that would be changed
            proposed_action: Dict with action details (function to call, args, etc)
            risk_level: low, medium, high

        Returns:
            Change ID
        """
        queue = self._load_queue()

        # Generate unique ID
        change_id = hashlib.md5(
            f"{title}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]

        change = {
            "id": change_id,
            "title": title,
            "description": description,
            "change_type": change_type,
            "files_affected": files_affected,
            "proposed_action": proposed_action,
            "risk_level": risk_level,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }

        queue["pending"].append(change)
        self._save_queue(queue)

        return change_id

    def get_pending(self) -> List[Dict]:
        """Get all pending changes."""
        queue = self._load_queue()
        return queue.get("pending", [])

    def get_change(self, change_id: str) -> Optional[Dict]:
        """Get specific change by ID."""
        queue = self._load_queue()

        for change in queue.get("pending", []):
            if change["id"] == change_id:
                return change

        for change in queue.get("approved", []):
            if change["id"] == change_id:
                return change

        for change in queue.get("rejected", []):
            if change["id"] == change_id:
                return change

        return None

    def approve(self, change_id: str) -> bool:
        """
        Approve a change and move it to approved queue.
        Returns True if successful.
        """
        queue = self._load_queue()

        # Find change in pending
        for i, change in enumerate(queue["pending"]):
            if change["id"] == change_id:
                # Move to approved
                change["status"] = "approved"
                change["approved_at"] = datetime.now().isoformat()
                queue["approved"].append(change)
                queue["pending"].pop(i)
                self._save_queue(queue)
                return True

        return False

    def reject(self, change_id: str, reason: str = "") -> bool:
        """
        Reject a change and move it to rejected queue.
        Returns True if successful.
        """
        queue = self._load_queue()

        # Find change in pending
        for i, change in enumerate(queue["pending"]):
            if change["id"] == change_id:
                # Move to rejected
                change["status"] = "rejected"
                change["rejected_at"] = datetime.now().isoformat()
                change["rejection_reason"] = reason
                queue["rejected"].append(change)
                queue["pending"].pop(i)
                self._save_queue(queue)
                return True

        return False

    def execute_approved(self, change_id: str) -> Dict:
        """
        Execute an approved change.
        Returns result dict with success status and details.
        """
        change = self.get_change(change_id)

        if not change:
            return {"success": False, "error": "Change not found"}

        if change["status"] != "approved":
            return {"success": False, "error": "Change not approved"}

        # Execute the proposed action
        action = change.get("proposed_action", {})
        action_type = action.get("type")

        try:
            if action_type == "edit_file":
                # Edit file
                file_path = action["file_path"]
                old_content = action["old_content"]
                new_content = action["new_content"]

                with open(file_path, 'r') as f:
                    current = f.read()

                if old_content in current:
                    updated = current.replace(old_content, new_content)
                    with open(file_path, 'w') as f:
                        f.write(updated)
                    return {"success": True, "message": f"Edited {file_path}"}
                else:
                    return {"success": False, "error": "Old content not found in file"}

            elif action_type == "write_file":
                # Write new file
                file_path = action["file_path"]
                content = action["content"]

                with open(file_path, 'w') as f:
                    f.write(content)
                return {"success": True, "message": f"Created {file_path}"}

            elif action_type == "bash_command":
                # Execute bash command
                import subprocess
                cmd = action["command"]
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return {
                    "success": result.returncode == 0,
                    "message": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None
                }

            else:
                return {"success": False, "error": f"Unknown action type: {action_type}"}

        except Exception as e:
            return {"success": False, "error": str(e)}


def send_approval_notification(change_id: str, change: Dict):
    """Send Telegram notification for pending approval."""
    import requests
    from pathlib import Path

    bot_token = None
    chat_id = None

    # Check existing credential locations (matching system patterns)
    tg_env_paths = [
        Path.home() / "hands-off/state/tg/bots/handsoff.env",
        Path("termux-hands-off/state/tg/bots/handsoff.env"),
        Path("/root/hands-off/state/tg/bots/handsoff.env"),
        Path("state/tg/bots/handsoff.env"),
    ]

    for env_path in tg_env_paths:
        if env_path.exists():
            try:
                for line in env_path.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("TOKEN="):
                        bot_token = line.split("=", 1)[1].strip()
                    elif line.startswith("CHAT_ID="):
                        chat_id = line.split("=", 1)[1].strip()
                if bot_token and chat_id:
                    break
            except Exception:
                continue

    # Fallback to env vars (multiple patterns)
    if not bot_token:
        bot_token = os.getenv("TG_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TOKEN")
    if not chat_id:
        chat_id = os.getenv("TG_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")

    if not bot_token or not chat_id:
        print(f"Telegram not configured. Change {change_id} pending approval.")
        return

    # Format notification message
    risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}
    emoji = risk_emoji.get(change.get("risk_level", "medium"), "🟡")

    message = f"""{emoji} **Approval Required**

**Change #{change_id}**
{change['title']}

**Type:** {change['change_type']}
**Risk:** {change['risk_level']}

**Description:**
{change['description']}

**Files affected:**
{', '.join(change['files_affected'])}

To approve: `/approve {change_id}`
To reject: `/reject {change_id}`
"""

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")


def needs_approval(change_type: str, files: List[str]) -> bool:
    """
    Determine if a change needs approval or can be auto-applied.

    Args:
        change_type: Type of change
        files: List of files being changed

    Returns:
        True if approval needed, False if safe to auto-apply
    """
    # Always require approval for these types
    risky_types = [
        "trading_parameters",
        "strategy",
        "algorithm",
        "configuration",
        "cron",
        "system_architecture"
    ]

    if change_type in risky_types:
        return True

    # Check file patterns
    risky_patterns = [
        "executor/",
        "alpha/",
        "config",
        ".env",
        "crontab"
    ]

    for file in files:
        for pattern in risky_patterns:
            if pattern in file:
                return True

    # Safe to auto-apply
    return False


if __name__ == "__main__":
    # Test
    queue = ApprovalQueue()

    # Add test change
    change_id = queue.add_change(
        title="Update risk limit from $100 to $200",
        description="Increasing max position size to take advantage of higher edge signals",
        change_type="trading_parameters",
        files_affected=["config/risk_limits.json"],
        proposed_action={
            "type": "edit_file",
            "file_path": "/root/hands-off-engine/config/risk_limits.json",
            "old_content": '"max_position": 100',
            "new_content": '"max_position": 200'
        },
        risk_level="high"
    )

    print(f"Created change: {change_id}")
    print(f"Pending changes: {len(queue.get_pending())}")
