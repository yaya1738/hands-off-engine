#!/usr/bin/env python3
"""Bounded bridge from the shared Factory control channel into Node1 safe tasks."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from tools import factory_control_channel as control_channel

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAIMED = REPO_ROOT / "state" / "factory_control_bridge_state.json"
BUS = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"

SAFE_ACTIONS = frozenset({
    "health_check",
    "system_status",
    "read_file_fact",
    "list_backends",
    "list_parties",
    "bus_summary",
    "test_status",
    "lifecycle_summary",
})


def _load_claimed() -> set[str]:
    try:
        value = json.loads(CLAIMED.read_text(encoding="utf-8"))
        return set(str(x) for x in value.get("claimed", []))
    except Exception:
        return set()


def _save_claimed(ids: set[str]) -> None:
    CLAIMED.parent.mkdir(parents=True, exist_ok=True)
    tmp = CLAIMED.with_suffix(".tmp")
    tmp.write_text(json.dumps({"claimed": sorted(ids)[-5000:]}) + "\n", encoding="utf-8")
    tmp.replace(CLAIMED)


def poll_once(max_commands: int = 1) -> int:
    """Admit at most max_commands safe Factory commands; never executes Factory authority."""
    claimed = _load_claimed()
    admitted = 0
    for command in control_channel.pending_commands(REPO_ROOT, claimed):
        if admitted >= max_commands:
            break
        command_id = str(command.get("id", "")).strip()
        if not command_id:
            continue
        metadata = command.get("metadata")
        if not isinstance(metadata, dict) or command.get("source") != "factory":
            claimed.add(command_id)
            continue
        action = str(metadata.get("action", "")).strip()
        if action not in SAFE_ACTIONS:
            claimed.add(command_id)
            continue

        task_id = f"control-{command_id}"
        params = metadata.get("params")
        if not isinstance(params, dict):
            params = {}
        task = {
            "from": "factory",
            "to": "anyclaw",
            "type": "task_assignment",
            "message": str(command.get("objective", ""))[:240],
            "msg_id": f"factory-control-{command_id}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": {
                "task_id": task_id,
                "action": action,
                "params": params,
                "reply_to": command_id,
                "correlation_id": str(metadata.get("correlation_id") or command_id),
                "factory_control_command_id": command_id,
                "source": "factory_control_channel",
                "execution_enabled": False,
            },
        }
        BUS.parent.mkdir(parents=True, exist_ok=True)
        with BUS.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(task, sort_keys=True) + "\n")
        claimed.add(command_id)
        admitted += 1

    _save_claimed(claimed)
    return admitted


if __name__ == "__main__":
    print(json.dumps({"admitted": poll_once()}, sort_keys=True))
