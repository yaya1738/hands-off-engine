#!/usr/bin/env python3
"""Fail-closed long-running root for the autonomous lifecycle.

The root is the durable authority-observation boundary.  It classifies queued
commands through governed_authority and records the latest decision without
ever granting executor authority.
"""
import json
import os
import signal
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

from governed_authority import authorize

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
STATUS = STATE / "governed_root_status.json"
QUEUE = STATE / "command_queue.jsonl"
APPROVALS = STATE / "approval_queue.json"
DECISIONS = STATE / "governed_decisions.json"

stop = False


def handle_stop(signum, _frame):
    global stop
    stop = True


def queue_counts():
    pending = 0
    if QUEUE.exists():
        for line in QUEUE.read_text().splitlines():
            try:
                if json.loads(line).get("status") == "pending":
                    pending += 1
            except Exception:
                continue
    approval_pending = 0
    if APPROVALS.exists():
        try:
            approval_pending = len(json.loads(APPROVALS.read_text()).get("pending", []))
        except Exception:
            pass
    return pending, approval_pending


def pending_commands():
    if not QUEUE.exists():
        return []
    commands = []
    for line in QUEUE.read_text().splitlines():
        try:
            command = json.loads(line)
            if command.get("status") == "pending":
                commands.append(command)
        except Exception:
            continue
    return commands


def load_decisions():
    if DECISIONS.exists():
        try:
            data = json.loads(DECISIONS.read_text())
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def record_decisions():
    decisions = load_decisions()
    changed = False
    for command in pending_commands():
        command_id = str(command.get("id") or command.get("command_id") or "")
        if not command_id:
            continue
        decision = authorize(command).to_dict()
        fingerprint = {
            "command_id": decision["command_id"],
            "decision": decision["decision"],
            "reason": decision["reason"],
            "execution_enabled": decision["execution_enabled"],
            "approval_required": decision["approval_required"],
            "command_status": command.get("status"),
            "approval_status": command.get("approval_status"),
        }
        if decisions.get(command_id) != fingerprint:
            decisions[command_id] = fingerprint
            changed = True
    if changed or not DECISIONS.exists():
        DECISIONS.write_text(json.dumps(decisions, indent=2, sort_keys=True) + "\n")
    return decisions


signal.signal(signal.SIGTERM, handle_stop)
signal.signal(signal.SIGINT, handle_stop)
signal.signal(signal.SIGHUP, signal.SIG_IGN)
STATE.mkdir(parents=True, exist_ok=True)

while not stop:
    decisions = record_decisions()
    pending_commands_count, pending_approvals = queue_counts()
    STATUS.write_text(json.dumps({
        "status": "running",
        "authority": "governed_authority",
        "execution_enabled": False,
        "pending_commands": pending_commands_count,
        "pending_approvals": pending_approvals,
        "governed_decisions": len(decisions),
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")
    time.sleep(10)

STATUS.write_text(json.dumps({
    "status": "stopped",
    "authority": "governed_authority",
    "execution_enabled": False,
}, indent=2) + "\n")
