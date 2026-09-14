#!/usr/bin/env python3
"""Fail-closed long-running root for the autonomous lifecycle.

The root is the durable authority-observation boundary. It classifies queued
commands through governed_authority and records the latest decision without
ever granting executor authority.

Paths are instance-rooted: derived from ``repo_root()`` instead of
``__file__``. Call ``set_repo_root(path)`` before starting to isolate
different instances (e.g. for testing or multi-repo setups).
"""
import json
import os
import signal
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from .governed_authority import authorize
except ImportError:
    from governed_authority import authorize

_ROOT_PATH = Path(__file__).resolve().parent.parent


def repo_root() -> Path:
    return _ROOT_PATH


def set_repo_root(path) -> None:
    global _ROOT_PATH
    _ROOT_PATH = Path(path)


def _resolve_status() -> Path:
    return _ROOT_PATH / "state" / "governed_root_status.json"


def _resolve_queue() -> Path:
    return _ROOT_PATH / "state" / "command_queue.jsonl"


def _resolve_approvals() -> Path:
    return _ROOT_PATH / "state" / "approval_queue.json"


def _resolve_decisions() -> Path:
    return _ROOT_PATH / "state" / "governed_decisions.json"


stop = False


def handle_stop(signum, _frame):
    global stop
    stop = True


def queue_counts():
    queue = _resolve_queue()
    approvals = _resolve_approvals()
    pending = 0
    if queue.exists():
        for line in queue.read_text().splitlines():
            try:
                if json.loads(line).get("status") == "pending":
                    pending += 1
            except Exception:
                continue
    approval_pending = 0
    if approvals.exists():
        try:
            approval_pending = len(json.loads(approvals.read_text()).get("pending", []))
        except Exception:
            pass
    return pending, approval_pending


def pending_commands():
    queue = _resolve_queue()
    if not queue.exists():
        return []
    commands = []
    for line in queue.read_text().splitlines():
        try:
            command = json.loads(line)
            if command.get("status") == "pending":
                commands.append(command)
        except Exception:
            continue
    return commands


def load_decisions():
    decisions_file = _resolve_decisions()
    if decisions_file.exists():
        try:
            data = json.loads(decisions_file.read_text())
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def record_decisions():
    decisions = load_decisions()
    decisions_file = _resolve_decisions()
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
    if changed or not decisions_file.exists():
        decisions_file.parent.mkdir(parents=True, exist_ok=True)
        decisions_file.write_text(json.dumps(decisions, indent=2, sort_keys=True) + "\n")
    return decisions


def run_forever():
    global stop
    stop = False
    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    (_ROOT_PATH / "state").mkdir(parents=True, exist_ok=True)

    while not stop:
        decisions = record_decisions()
        pending_commands_count, pending_approvals = queue_counts()
        _resolve_status().write_text(json.dumps({
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

    _resolve_status().write_text(json.dumps({
        "status": "stopped",
        "authority": "governed_authority",
        "execution_enabled": False,
    }, indent=2) + "\n")


if __name__ == "__main__":
    run_forever()
