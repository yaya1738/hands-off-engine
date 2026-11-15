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
import fcntl

REPO_ROOT = Path(__file__).parent.parent
QUEUE_FILE = REPO_ROOT / "state" / "approval_queue.json"
APPROVAL_MAX_AGE_SECONDS = 24 * 60 * 60


class ApprovalQueue:
    """Manages pending changes requiring user approval."""

    def __init__(self, repo_root=None, queue_file=None):
        self.repo_root = Path(repo_root).resolve() if repo_root is not None else REPO_ROOT.resolve()
        if queue_file is not None:
            self.queue_file = Path(queue_file)
        elif repo_root is not None:
            self.queue_file = self.repo_root / "state" / "approval_queue.json"
        else:
            self.queue_file = QUEUE_FILE
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

    def _resolve_repo_path(self, file_path: str) -> Path:
        """Resolve an action path and reject traversal or symlink escapes."""
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError("file_path must be a non-empty string")
        candidate = Path(file_path)
        if not candidate.is_absolute():
            candidate = self.repo_root / candidate
        resolved = candidate.resolve(strict=False)
        try:
            resolved.relative_to(self.repo_root)
        except ValueError:
            raise ValueError("file action path must remain inside the repository root")
        return resolved

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

    def format_change_preview(self, change: Dict) -> str:
        """Describe the authority surface without exposing file contents."""
        action = change.get("proposed_action") or {}
        action_type = action.get("type", "unknown")
        lines = [
            "Description: " + str(change.get("description", "No description provided")),
            "Files affected: " + (", ".join(change.get("files_affected") or []) or "Not specified"),
            "Action type: " + str(action_type),
        ]
        target = action.get("file_path")
        if target:
            lines.append("Target: " + str(target))
        if action_type == "bash_command":
            lines.append("Execution: BLOCKED — arbitrary shell commands are disabled")
        elif action_type in {"edit_file", "write_file"}:
            lines.append("Execution boundary: repository-local file change only")
        return "\n".join(lines)

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
                action_bytes = json.dumps(change.get("proposed_action", {}), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                change["approved_action_sha256"] = hashlib.sha256(action_bytes).hexdigest()
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
        """Execute an approved change once, only if its approved action is unchanged."""
        lock_path = self.queue_file.with_name(self.queue_file.name + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "a+") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            queue = self._load_queue()
            change = next((item for item in queue.get("approved", []) if item.get("id") == change_id), None)
            if change is None:
                if any(item.get("id") == change_id for item in queue.get("pending", [])):
                    return {"success": False, "error": "Change not approved"}
                return {"success": False, "error": "Change not found"}
            if change.get("status") != "approved":
                return {"success": False, "error": f"Approval is not executable (status={change.get('status')})"}
            try:
                approved_at = datetime.fromisoformat(change["approved_at"])
                now = datetime.now(approved_at.tzinfo) if approved_at.tzinfo else datetime.now()
                approval_age = (now - approved_at).total_seconds()
            except (KeyError, TypeError, ValueError):
                return {"success": False, "error": "Approval timestamp missing or invalid; create a new proposal"}
            if approval_age < 0 or approval_age > APPROVAL_MAX_AGE_SECONDS:
                return {"success": False, "error": "Approval expired; create a new proposal"}
            action = change.get("proposed_action", {})
            action_bytes = json.dumps(action, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            current_digest = hashlib.sha256(action_bytes).hexdigest()
            approved_digest = change.get("approved_action_sha256")
            if not isinstance(approved_digest, str) or not __import__("hmac").compare_digest(approved_digest, current_digest):
                return {"success": False, "error": "Approved action changed after approval; create a new proposal"}
            change["status"] = "executing"
            change["execution_started_at"] = datetime.now().isoformat()
            self._save_queue(queue)
            result = self._execute_action(action)
            change["status"] = "executed" if result.get("success") else "execution_failed"
            change["executed_at"] = datetime.now().isoformat()
            change["execution_result"] = result
            self._save_queue(queue)
            return result

    def _execute_action(self, action: Dict) -> Dict:
        """Execute only narrow repository-local file actions allowed by policy."""
        action_type = action.get("type")
        try:
            if action_type == "edit_file":
                file_path = self._resolve_repo_path(action["file_path"])
                old_content = action["old_content"]
                new_content = action["new_content"]
                if not isinstance(old_content, str) or not old_content:
                    return {"success": False, "error": "old_content must be a non-empty exact match"}
                if not isinstance(new_content, str):
                    return {"success": False, "error": "new_content must be a string"}
                if not file_path.is_file():
                    return {"success": False, "error": "edit target must be an existing regular file"}
                current = file_path.read_text(encoding="utf-8")
                match_count = current.count(old_content)
                if match_count != 1:
                    return {"success": False, "error": f"old_content must match exactly once; found {match_count} matches"}
                updated = current.replace(old_content, new_content, 1)
                file_path.write_text(updated, encoding="utf-8")
                return {"success": True, "message": f"Edited {file_path.relative_to(self.repo_root)}"}
            if action_type == "write_file":
                file_path = self._resolve_repo_path(action["file_path"])
                content = action["content"]
                if not isinstance(content, str):
                    return {"success": False, "error": "content must be a string"}
                if file_path.exists():
                    return {"success": False, "error": "write_file is create-only; target already exists"}
                if not file_path.parent.is_dir():
                    return {"success": False, "error": "parent directory must already exist"}
                with file_path.open("x", encoding="utf-8") as handle:
                    handle.write(content)
                return {"success": True, "message": f"Created {file_path.relative_to(self.repo_root)}"}
            if action_type == "bash_command":
                return {"success": False, "error": "arbitrary bash_command actions are disabled; use the governed executor allowlist"}
            return {"success": False, "error": f"Unknown action type: {action_type}"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


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
    action_preview = ApprovalQueue().format_change_preview(change)

    message = f"""{emoji} **Approval Required**

**Change #{change_id}**
{change['title']}

**Type:** {change['change_type']}
**Risk:** {change['risk_level']}

**Description:**
{change['description']}

**Files affected:**
{', '.join(change['files_affected'])}

**Action preview:**
{action_preview}

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
