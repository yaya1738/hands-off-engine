#!/usr/bin/env python3
"""
Proactive Status Update System

Sends regular updates to user about what the system is:
- Currently working on
- Planning to do
- Has accomplished
- Thinking about

Creates the "proactive partner" relationship where user sees
system thinking and working, not just silent until approval needed.
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import os
import json
import sys
from datetime import datetime, timedelta
from typing import List, Dict

REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
METRICS_FILE = STATE_DIR / "performance_metrics.jsonl"
TASK_QUEUE = STATE_DIR / "autonomous_task_queue.json"
APPROVAL_QUEUE = STATE_DIR / "approval_queue.json"


def get_telegram_config():
    """Get Telegram bot credentials."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    return bot_token, chat_id


def send_telegram(message: str):
    """Send message via Telegram."""
    try:
        import requests
        bot_token, chat_id = get_telegram_config()

        if not bot_token or not chat_id:
            print("Telegram not configured")
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return True

    except Exception as e:
        print(f"Error sending Telegram: {e}")
        return False


def get_recent_activity() -> Dict:
    """Analyze recent system activity."""
    if not METRICS_FILE.exists():
        return {"runs": 0, "orders": 0}

    # Get last 24 hours
    cutoff = datetime.now() - timedelta(hours=24)
    recent = []

    with open(METRICS_FILE) as f:
        for line in f:
            try:
                metric = json.loads(line)
                ts = datetime.fromisoformat(metric["timestamp"].replace("+00:00", ""))
                if ts >= cutoff:
                    recent.append(metric)
            except:
                continue

    if not recent:
        return {"runs": 0, "orders": 0}

    total_orders = sum(m.get("execution_plan", {}).get("total_orders", 0) for m in recent)
    total_size = sum(m.get("execution_plan", {}).get("total_size_usd", 0) for m in recent)
    avg_edge = sum(m.get("alpha_signals", {}).get("avg_edge", 0) for m in recent) / len(recent)

    return {
        "runs": len(recent),
        "orders": total_orders,
        "size": total_size,
        "avg_edge": avg_edge * 100
    }


def get_current_tasks() -> List[Dict]:
    """Get tasks system is working on."""
    if not TASK_QUEUE.exists():
        return []

    with open(TASK_QUEUE) as f:
        data = json.load(f)
        return data.get("tasks", [])


def get_pending_approvals() -> List[Dict]:
    """Get changes pending user approval."""
    if not APPROVAL_QUEUE.exists():
        return []

    with open(APPROVAL_QUEUE) as f:
        data = json.load(f)
        return data.get("pending", [])


def get_system_insights() -> List[str]:
    """Generate insights about system performance."""
    insights = []

    if not METRICS_FILE.exists():
        return insights

    # Get last week of data
    cutoff = datetime.now() - timedelta(days=7)
    metrics = []

    with open(METRICS_FILE) as f:
        for line in f:
            try:
                metric = json.loads(line)
                ts = datetime.fromisoformat(metric["timestamp"].replace("+00:00", ""))
                if ts >= cutoff:
                    metrics.append(metric)
            except:
                continue

    if len(metrics) < 10:
        return ["Still collecting data to generate insights"]

    # Calculate trends
    avg_selection = sum(m.get("alpha_signals", {}).get("selection_rate", 0) for m in metrics) / len(metrics)
    avg_edge = sum(m.get("alpha_signals", {}).get("avg_edge", 0) for m in metrics) / len(metrics)

    if avg_selection > 0.90:
        insights.append(f"Selection rate is high ({avg_selection*100:.0f}%) - alpha model needs tuning")

    if avg_edge > 0.08:
        insights.append(f"Strong edge detected ({avg_edge*100:.1f}%) - consider increasing position sizes")

    return insights if insights else ["System operating within normal parameters"]


def generate_update() -> str:
    """Generate proactive status update message."""
    activity = get_recent_activity()
    tasks = get_current_tasks()
    approvals = get_pending_approvals()
    insights = get_system_insights()

    # Build message
    msg = f"""📊 **System Status Update**
{datetime.now().strftime("%A, %B %d")}

**Last 24 Hours:**
• {activity['runs']} runs completed
• {activity['orders']} orders planned
• ${activity['size']:.0f} total size
• {activity['avg_edge']:.1f}% avg edge

"""

    # Current work
    if tasks:
        msg += f"**Currently Working On:**\n"
        for task in tasks[:3]:
            title = task['title'][:60]
            msg += f"• {title}\n"
        if len(tasks) > 3:
            msg += f"  ... and {len(tasks)-3} more\n"
        msg += "\n"

    # Pending approvals
    if approvals:
        msg += f"**⚠️ Needs Your Approval:** {len(approvals)}\n"
        for approval in approvals[:2]:
            msg += f"• {approval['title']}\n"
        msg += "Use /pending to review\n\n"

    # Insights
    if insights:
        msg += "**Insights:**\n"
        for insight in insights[:3]:
            msg += f"• {insight}\n"
        msg += "\n"

    # Status
    msg += "**Status:** Operating autonomously\n"
    msg += "**Mode:** DRYRUN (no real money)\n"
    msg += "\n"
    msg += "_Use /status for details, /help for commands_"

    return msg


def main():
    """Generate and send proactive update."""
    print("Generating proactive status update...")

    message = generate_update()
    print(f"\n{message}\n")

    if send_telegram(message):
        print("✓ Update sent via Telegram")
        return 0
    else:
        print("✗ Failed to send update")
        return 1


if __name__ == "__main__":
    sys.exit(main())
