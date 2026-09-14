#!/usr/bin/env python3
"""Improvement Approval — Telegram-based approve/reject workflow for risky improvements.

When the improvement applier queues risky actions for approval, this module:
1. Detects new queued items
2. Sends a Telegram notification with approve/reject instructions
3. Processes approve/reject responses from the operator
4. Executes approved improvements through the applier

Operator interaction:
- Bot sends: "Improvement pending: [title]. Reply /approve [id] or /reject [id]"
- Operator replies: /approve imp-abc123 or /reject imp-abc123
- Bot confirms and executes
"""

import json
import subprocess
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
APPROVAL_STATE = STATE / "improvement_approval_state.json"
APPLIER_STATE = STATE / "improvement_applier_state.json"
TELEGRAM_CONFIG = Path.home() / ".codex" / "telegram-bridge.json"


def load_approval_state():
    if APPROVAL_STATE.exists():
        try:
            return json.loads(APPROVAL_STATE.read_text())
        except Exception:
            pass
    return {"notified": [], "approved": [], "rejected": [], "executed": []}


def save_approval_state(state):
    APPROVAL_STATE.parent.mkdir(parents=True, exist_ok=True)
    APPROVAL_STATE.write_text(json.dumps(state, indent=2) + "\n")


def load_applier_state():
    if APPLIER_STATE.exists():
        try:
            return json.loads(APPLIER_STATE.read_text())
        except Exception:
            pass
    return {"queued": []}


def send_telegram(message: str):
    """Send a Telegram message to the operator."""
    if not TELEGRAM_CONFIG.exists():
        print(f"Telegram config not found at {TELEGRAM_CONFIG}")
        return False
    try:
        cfg = json.loads(TELEGRAM_CONFIG.read_text())
        token = cfg["botToken"]
        chat_id = cfg["chatIds"][0]

        data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode()
        import urllib.request
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        return result.get("ok", False)
    except Exception as e:
        print(f"Telegram send error: {e}")
        return False


def check_and_notify():
    """Check for new queued improvements and send Telegram notifications."""
    state = load_approval_state()
    applier_state = load_applier_state()
    queued = applier_state.get("queued", [])
    notified_ids = set(state.get("notified", []))

    new_items = []
    for item in queued:
        if item["id"] not in notified_ids:
            new_items.append(item)

    if not new_items:
        return {"new_notifications": 0}

    for item in new_items:
        msg = (
            f"🔒 Improvement pending approval\n\n"
            f"Title: {item.get('title', 'Unknown')}\n"
            f"Category: {item.get('category', '?')}\n"
            f"Action: {item.get('action', '?')}\n"
            f"ID: {item['id'][:20]}\n\n"
            f"Reply /approve {item['id'][:20]} to approve\n"
            f"Reply /reject {item['id'][:20]} to reject"
        )
        sent = send_telegram(msg)
        if sent:
            state.setdefault("notified", []).append(item["id"])

    save_approval_state(state)
    return {"new_notifications": len(new_items)}


def process_approval(imp_id_prefix: str, approved: bool) -> dict:
    """Process an approve/reject response for a queued improvement."""
    state = load_approval_state()
    applier_state = load_applier_state()
    queued = applier_state.get("queued", [])

    # Find matching item by ID prefix
    matched = None
    for item in queued:
        if item["id"].startswith(imp_id_prefix):
            matched = item
            break

    if not matched:
        return {"processed": False, "reason": f"No queued improvement matching '{imp_id_prefix}'"}

    if approved:
        state.setdefault("approved", []).append(matched["id"])
        # Remove from queued
        queued[:] = [q for q in queued if q["id"] != matched["id"]]
        applier_state["queued"] = queued

        # Execute through the applier
        try:
            from scripts.improvement_applier import ImprovementApplier
            applier = ImprovementApplier()
            applier.state = applier_state
            result = applier.approve_improvement(matched["id"])
            if result.get("approved"):
                state.setdefault("executed", []).append(matched["id"])
                send_telegram(f"✅ Approved and executed: {matched.get('title', matched['id'][:20])}")
            else:
                send_telegram(f"⚠️ Approved but execution failed: {result.get('reason', 'unknown')}")
        except Exception as e:
            send_telegram(f"⚠️ Approved but execution error: {e}")
    else:
        state.setdefault("rejected", []).append(matched["id"])
        queued[:] = [q for q in queued if q["id"] != matched["id"]]
        applier_state["queued"] = queued
        send_telegram(f"❌ Rejected: {matched.get('title', matched['id'][:20])}")

    # Save both states
    save_approval_state(state)
    APPLIER_STATE.write_text(json.dumps(applier_state, indent=2) + "\n")

    return {"processed": True, "approved": approved, "id": matched["id"], "title": matched.get("title")}


def status() -> dict:
    state = load_approval_state()
    applier_state = load_applier_state()
    return {
        "pending": len(applier_state.get("queued", [])),
        "approved_total": len(state.get("approved", [])),
        "rejected_total": len(state.get("rejected", [])),
        "executed_total": len(state.get("executed", [])),
        "notified_total": len(state.get("notified", [])),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Improvement Approval Workflow")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("check", help="Check for new queued improvements and notify")
    sub.add_parser("status", help="Show approval status")

    approve_p = sub.add_parser("approve", help="Approve a queued improvement")
    approve_p.add_argument("id", help="Improvement ID prefix")

    reject_p = sub.add_parser("reject", help="Reject a queued improvement")
    reject_p.add_argument("id", help="Improvement ID prefix")

    args = parser.parse_args()

    if args.cmd == "check":
        result = check_and_notify()
        print(json.dumps(result, indent=2))
    elif args.cmd == "approve":
        result = process_approval(args.id, approved=True)
        print(json.dumps(result, indent=2))
    elif args.cmd == "reject":
        result = process_approval(args.id, approved=False)
        print(json.dumps(result, indent=2))
    elif args.cmd == "status":
        print(json.dumps(status(), indent=2))
    else:
        parser.print_help()
