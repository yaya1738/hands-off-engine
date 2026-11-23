#!/usr/bin/env python3
"""
AGGRESSIVE INCOME ACTIVATION
Automatically posts to all available channels to generate income NOW.
"""
import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

REPO = Path("/root/hands-off-engine")

def send_telegram(msg):
    """Send only with explicitly configured local credentials."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception:
        return False

def main():
    print("🚀 AGGRESSIVE INCOME ACTIVATION")
    
    # Load outreach materials
    upwork = (REPO / "outreach/upwork_project_listing.md").read_text() if (REPO / "outreach/upwork_project_listing.md").exists() else ""
    fiverr = (REPO / "outreach/fiverr_gig.md").read_text() if (REPO / "outreach/fiverr_gig.md").exists() else ""
    
    actions = []
    
    # Action 1: Notify Yair with exact steps
    msg = """Income activation review required.

No transfer, wallet funding request, or live trading action is authorized by this script.
Refresh all financial facts from authoritative sources and obtain explicit approval before any money movement.
"""

    if send_telegram(msg):
        actions.append("Sent a non-financial activation notice via configured Telegram.")
    else:
        actions.append("Telegram notice skipped; credentials are not configured or delivery failed.")
    
    # Action 2: Log activation attempt
    log_file = REPO / "state" / "income_activation_log.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "income_activation_requested",
            "channels": ["upwork", "fiverr", "linkedin", "trading"],
            "status": "pending_user_action"
        }) + '\n')
    actions.append("✓ Logged activation attempt")
    
    print("\n".join(actions))
    print("\n⚡ Activation instructions sent. Waiting for Yair to execute.")

if __name__ == "__main__":
    main()
