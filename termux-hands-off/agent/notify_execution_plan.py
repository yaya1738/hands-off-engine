#!/usr/bin/env python3
"""
Notify Execution Plan

Reads executor/execution_plan.json and pushes a concise summary
to Telegram and IFTTT for mobile review.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def read_env(path):
    """Read .env file into a dictionary"""
    d = {}
    if not os.path.exists(path):
        return d
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def send_telegram(msg, env_path):
    """Send message via Telegram"""
    e = read_env(env_path)
    token = e.get("TOKEN")
    chat = e.get("CHAT_ID")

    if not token or not chat:
        print(f"[skip] Telegram: missing TOKEN or CHAT_ID in {env_path}")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat,
        "text": msg,
        "parse_mode": "HTML"
    }).encode()

    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            payload = json.loads(r.read().decode())

        if payload.get("ok") is True:
            print("[ok] Telegram sent")
            return True
        else:
            print(f"[err] Telegram API: {payload}")
            return False
    except Exception as e:
        print(f"[err] Telegram failed: {e}")
        return False


def send_ifttt(msg, env_path):
    """Send message via IFTTT webhook"""
    e = read_env(env_path)
    webhook_key = e.get("IFTTT_WEBHOOK_KEY")
    event_name = e.get("IFTTT_EVENT_NAME", "execution_plan")

    if not webhook_key:
        print(f"[skip] IFTTT: missing IFTTT_WEBHOOK_KEY in {env_path}")
        return False

    url = f"https://maker.ifttt.com/trigger/{event_name}/with/key/{webhook_key}"
    data = json.dumps({
        "value1": msg,
        "value2": "",
        "value3": ""
    }).encode()

    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            response = r.read().decode()

        print(f"[ok] IFTTT sent: {response}")
        return True
    except Exception as e:
        print(f"[err] IFTTT failed: {e}")
        return False


def format_execution_plan(plan_data):
    """Format execution plan as mobile-friendly message"""
    dryrun = plan_data.get("dryrun", True)
    total_orders = plan_data.get("total_orders", 0)
    total_size = plan_data.get("total_size_usd", 0)
    timestamp = plan_data.get("timestamp", "unknown")

    # Build summary header
    mode = "🔵 DRYRUN" if dryrun else "🔴 LIVE"
    lines = [
        f"<b>{mode} Execution Plan</b>",
        f"",
        f"📊 <b>Summary:</b> {total_orders} orders, ${total_size:.0f} total",
        f"⏰ {timestamp[:19]}",  # Truncate timestamp
        f""
    ]

    # Add individual orders
    if total_orders > 0:
        lines.append("<b>Orders:</b>")
        orders = plan_data.get("orders", [])
        for i, order in enumerate(orders, 1):
            question = order.get("question", "Unknown")
            side = order.get("side", "?")
            size = order.get("size_usd", 0)
            edge = order.get("edge", 0)
            category = order.get("category", "?")

            # Truncate long questions for mobile
            if len(question) > 50:
                question = question[:47] + "..."

            lines.append(
                f"{i}. [{category}] {question}\n"
                f"   {side} • ${size} • Edge: {edge:.1%}"
            )

        lines.append(f"")
        lines.append(f"📍 Review full plan in execution_plan.json")
    else:
        lines.append("<i>No orders to execute</i>")

    return "\n".join(lines)


def main():
    # Paths
    repo_root = Path(__file__).parent.parent.parent
    plan_path = repo_root / "executor" / "execution_plan.json"

    # Try multiple env file locations
    env_locations = [
        os.path.expanduser("~/hands-off/state/tg/bots/handsoff.env"),
        os.path.expanduser("~/hands-off/handsoff.env"),
        repo_root / "termux-hands-off" / "handsoff.env",
    ]

    ifttt_env_locations = [
        os.path.expanduser("~/hands-off/ifttt.env"),
        repo_root / "termux-hands-off" / "ifttt.env",
    ]

    # Find first existing env file
    telegram_env = next((str(p) for p in env_locations if os.path.exists(p)), None)
    ifttt_env = next((str(p) for p in ifttt_env_locations if os.path.exists(p)), None)

    if not telegram_env and not ifttt_env:
        print("[err] No notification credentials found")
        print(f"      Checked: {[str(p) for p in env_locations + ifttt_env_locations]}")
        return 1

    # Read execution plan
    if not plan_path.exists():
        print(f"[err] Execution plan not found: {plan_path}")
        return 1

    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    # Format message
    message = format_execution_plan(plan_data)

    print("=" * 60)
    print("Sending notification:")
    print("=" * 60)
    print(message)
    print("=" * 60)

    # Send notifications
    success = False

    if telegram_env:
        if send_telegram(message, telegram_env):
            success = True

    if ifttt_env:
        if send_ifttt(message, ifttt_env):
            success = True

    if not success:
        print("[err] All notification methods failed")
        return 1

    print("[ok] Notification sent successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
