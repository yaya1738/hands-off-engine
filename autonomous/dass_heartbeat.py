#!/usr/bin/env python3
"""One-shot, fail-closed DASS heartbeat.

This intentionally performs observation/authorization only. It never enables
LIVE execution and exits after one bounded cycle so an external scheduler can
provide the durable heartbeat.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from .governed_authority import authorize

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
QUEUE = STATE / "command_queue.jsonl"
DECISIONS = STATE / "governed_decisions.json"
STATUS = STATE / "dass_heartbeat_status.json"


def heartbeat():
    STATE.mkdir(parents=True, exist_ok=True)
    decisions = {}
    if DECISIONS.exists():
        try:
            loaded = json.loads(DECISIONS.read_text())
            if isinstance(loaded, dict):
                decisions.update(loaded)
        except Exception:
            pass

    processed = 0
    if QUEUE.exists():
        for line in QUEUE.read_text().splitlines():
            try:
                command = json.loads(line)
            except Exception:
                continue
            if command.get("status") != "pending":
                continue
            command_id = str(command.get("id") or command.get("command_id") or "")
            if not command_id:
                continue
            decision = authorize(command).to_dict()
            decisions[command_id] = {
                "command_id": decision["command_id"],
                "decision": decision["decision"],
                "reason": decision["reason"],
                "execution_enabled": False,
                "approval_required": decision["approval_required"],
                "command_status": command.get("status"),
                "approval_status": command.get("approval_status"),
            }
            processed += 1

    DECISIONS.write_text(json.dumps(decisions, indent=2, sort_keys=True) + "\n")
    status = {
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processed_commands": processed,
        "governed_decisions": len(decisions),
        "execution_enabled": False,
        "fail_closed": True,
    }
    STATUS.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    return status


if __name__ == "__main__":
    print(json.dumps(heartbeat(), sort_keys=True))
