#!/usr/bin/env python3
"""Durable, idempotent projection of task lifecycle from the canonical bus.

The coordination bus remains the source of truth. This module materializes a
small machine-readable view keyed by task_id so Factory, AnyClaw, and the
Control Room can observe the same lifecycle without creating another bus.

Projection state is local to the checkout and may be rebuilt from
ai/coordination/messages.jsonl at any time.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
MESSAGES_FILE = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
LIFECYCLE_FILE = REPO_ROOT / "state" / "task_lifecycle.json"

STATES = (
    "sent",
    "claimed",
    "executing",
    "completed",
    "result_published",
    "observed",
)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _task_id(message: Dict) -> Optional[str]:
    context = message.get("context") or {}
    return context.get("task_id") or message.get("task_id")


def _load(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def _entry(task_id: str, message: Dict) -> Dict:
    context = message.get("context") or {}
    return {
        "task_id": task_id,
        "sender": message.get("from"),
        "recipient": message.get("to"),
        "action": context.get("action"),
        "correlation_id": context.get("correlation_id") or context.get("reply_to"),
        "states": {},
        "updated_at": message.get("timestamp") or _now(),
    }


def apply_message(state: Dict, message: Dict) -> bool:
    """Apply one canonical message; return True only when state changes."""
    task_id = _task_id(message)
    if not task_id:
        return False

    entry = state.setdefault(task_id, _entry(task_id, message))
    context = message.get("context") or {}
    msg_type = message.get("type")
    sender = message.get("from")
    recipient = message.get("to")
    changed = False

    if not entry.get("sender") and sender:
        entry["sender"] = sender
        changed = True
    if not entry.get("recipient") and recipient:
        entry["recipient"] = recipient
        changed = True
    if context.get("action") and entry.get("action") != context["action"]:
        entry["action"] = context["action"]
        changed = True

    transitions = []
    if msg_type == "task_assignment":
        transitions.append("sent")
        if context.get("claimed") is True:
            transitions.append("claimed")
        if context.get("status") in ("executing", "running"):
            transitions.append("executing")
    elif msg_type == "task_claimed":
        transitions.append("claimed")
    elif msg_type in ("task_started", "task_executing"):
        transitions.append("executing")
    elif msg_type == "task_result":
        transitions.extend(("completed", "result_published"))
    elif msg_type == "continuation_event":
        event_type = context.get("event_type")
        if event_type in ("task_completed", "test_result"):
            transitions.append("completed")
        if context.get("observed") is True:
            transitions.append("observed")

    if context.get("observed") is True:
        transitions.append("observed")

    timestamp = message.get("timestamp") or _now()
    for transition in transitions:
        if transition not in entry["states"]:
            entry["states"][transition] = timestamp
            changed = True

    if changed:
        entry["updated_at"] = timestamp
        if context.get("status"):
            entry["status"] = context["status"]
        if context.get("result") is not None:
            entry["result_summary"] = str(context["result"])[:500]
        elif context.get("error"):
            entry["error"] = str(context["error"])[:500]
    return changed


class LifecycleProjector:
    """Incrementally project canonical messages into shared lifecycle state."""

    def __init__(self, repo_root=None, state_file=None):
        self.repo_root = Path(repo_root) if repo_root else REPO_ROOT
        self.messages_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"
        self.state_file = Path(state_file) if state_file else self.repo_root / "state" / "task_lifecycle.json"

    def project(self, messages: Optional[Iterable[Dict]] = None) -> Dict:
        state = _load(self.state_file)
        if messages is None:
            messages = self._read_messages()
        changed_tasks = set()
        for message in messages:
            if apply_message(state, message):
                task_id = _task_id(message)
                if task_id:
                    changed_tasks.add(task_id)
        _save(self.state_file, state)
        changed = len(changed_tasks)
        return {"tasks": len(state), "changed": changed, "state_file": str(self.state_file)}

    def _read_messages(self):
        if not self.messages_file.exists():
            return []
        rows = []
        with self.messages_file.open("r") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows

    def get(self, task_id: str) -> Optional[Dict]:
        return _load(self.state_file).get(task_id)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Project canonical task lifecycle")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--task-id", default=None)
    args = parser.parse_args()
    projector = LifecycleProjector(repo_root=args.repo_root)
    if args.task_id:
        print(json.dumps(projector.get(args.task_id), indent=2, sort_keys=True))
    else:
        print(json.dumps(projector.project(), indent=2, sort_keys=True))
