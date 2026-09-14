#!/usr/bin/env python3
"""Fail-closed long-running root for the autonomous lifecycle."""
import json
import os
import signal
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
STATUS = STATE / "governed_root_status.json"
QUEUE = STATE / "command_queue.jsonl"
APPROVALS = STATE / "approval_queue.json"

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

signal.signal(signal.SIGTERM, handle_stop)
signal.signal(signal.SIGINT, handle_stop)
signal.signal(signal.SIGHUP, signal.SIG_IGN)
STATE.mkdir(parents=True, exist_ok=True)

while not stop:
    pending_commands, pending_approvals = queue_counts()
    STATUS.write_text(json.dumps({
        "status": "running",
        "authority": "fail_closed",
        "execution_enabled": False,
        "pending_commands": pending_commands,
        "pending_approvals": pending_approvals,
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")
    time.sleep(10)

STATUS.write_text(json.dumps({"status": "stopped", "authority": "fail_closed", "execution_enabled": False}, indent=2) + "\n")
