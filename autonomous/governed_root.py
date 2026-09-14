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

stop = False

def handle_stop(signum, _frame):
    global stop
    stop = True

signal.signal(signal.SIGTERM, handle_stop)
signal.signal(signal.SIGINT, handle_stop)
signal.signal(signal.SIGHUP, signal.SIG_IGN)
STATE.mkdir(parents=True, exist_ok=True)

while not stop:
    STATUS.write_text(json.dumps({
        "status": "running",
        "authority": "fail_closed",
        "execution_enabled": False,
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")
    time.sleep(10)

STATUS.write_text(json.dumps({"status": "stopped", "authority": "fail_closed"}, indent=2) + "\n")
