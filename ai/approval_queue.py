#!/usr/bin/env python3
"""Legacy approval queue compatibility layer; never an execution authority."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).parent.parent
QUEUE_FILE = REPO_ROOT / "state" / "approval_queue.json"


class ApprovalQueue:
    """Persistent compatibility queue; never an execution authority."""

    def __init__(self):
        self.queue_file = QUEUE_FILE
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_queue(self) -> Dict:
        if not self.queue_file.exists():
            return {"pending": [], "approved": [], "rejected": []}
        with open(self.queue_file) as f:
            return json.load(f)

    def _save_queue(self, queue: Dict):
        with open(self.queue_file, "w") as f:
            json.dump(queue, f, indent=2)

    def add_change(self, title: str, description: str, change_type: str,
                   files_affected: List[str], proposed_action: Dict,
                   risk_level: str = "medium") -> str:
        queue = self._load_queue()
        change_id = hashlib.md5(f"{title}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        change = {
            "id": change_id, "title": title, "description": description,
            "change_type": change_type, "files_affected": files_affected,
            "proposed_action": proposed_action, "risk_level": risk_level,
            "created_at": datetime.now().isoformat(), "status": "pending",
        }
        queue["pending"].append(change)
        self._save_queue(queue)
        return change_id

    def get_pending(self) -> List[Dict]:
        return self._load_queue().get("pending", [])

    def get_change(self, change_id: str) -> Optional[Dict]:
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
        """Record approval only; never execute the proposed action."""
        queue = self._load_queue()
        for i, change in enumerate(queue["pending"]):
            if change["id"] == change_id:
                change["status"] = "approved"
                change["approved_at"] = datetime.now().isoformat()
                change["execution_authority"] = "factory_authority_gateway"
                queue["approved"].append(change)
                queue["pending"].pop(i)
                self._save_queue(queue)
                return True
        return False

    def reject(self, change_id: str, reason: str = "") -> bool:
        queue = self._load_queue()
        for i, change in enumerate(queue["pending"]):
            if change["id"] == change_id:
                change["status"] = "rejected"
                change["rejected_at"] = datetime.now().isoformat()
                change["rejection_reason"] = reason
                queue["rejected"].append(change)
                queue["pending"].pop(i)
                self._save_queue(queue)
                return True
        return False

    def execute_approved(self, change_id: str) -> Dict:
        """Fail closed: legacy queue cannot execute approved changes."""
        change = self.get_change(change_id)
        if not change:
            return {"success": False, "error": "Change not found"}
        if change["status"] != "approved":
            return {"success": False, "error": "Change not approved"}
        return {
            "success": False, "blocked": True,
            "error": "legacy_execution_authority_disabled",
            "message": "Approval recorded, but legacy execution is disabled. Route execution through FactoryAuthorityGateway.",
            "change_id": change_id,
        }


def send_approval_notification(change_id: str, change: Dict):
    """Send a notification using runtime-only Telegram credentials."""
    import os
    bot_token = os.getenv("TG_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print(f"Telegram not configured. Change {change_id} pending approval.")
        return

    import requests
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
        requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except Exception as exc:
        print(f"Error sending Telegram notification: {exc}")


def needs_approval(change_type: str, files: List[str]) -> bool:
    risky_types = ["trading_parameters", "strategy", "algorithm", "configuration", "cron", "system_architecture"]
    if change_type in risky_types:
        return True
    risky_patterns = ["executor/", "alpha/", "config", ".env", "crontab"]
    return any(pattern in file for file in files for pattern in risky_patterns)
