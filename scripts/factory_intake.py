#!/usr/bin/env python3
"""Factory-side continuation intake."""
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [FactoryIntake] %(message)s')
log = logging.getLogger("FactoryIntake")

REPO_ROOT = Path(__file__).resolve().parent.parent
MESSAGES_FILE = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
INTAKE_STATE = REPO_ROOT / "state" / "factory_intake_state.json"
DECISION_DIR = REPO_ROOT / "state" / "intake_decisions"
WAKE_EVENT_TYPES = frozenset({"task_completed", "blocked", "authorization_required", "security_boundary", "test_failure"})
TARGET_PARTY = "anyclaw"
EVENT_TYPE_FIELD_CANDIDATES = ("event_type", "type")


def _load_state(path: Optional[Path] = None) -> dict:
    state_path = Path(path) if path else INTAKE_STATE
    if state_path.exists():
        try:
            return json.loads(state_path.read_text())
        except Exception:
            pass
    return {"consumed_ids": [], "decisions": []}


def _save_state(state: dict, path: Optional[Path] = None):
    state_path = Path(path) if path else INTAKE_STATE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n")


def _get_event_type(event: dict) -> str:
    context = event.get("context") or {}
    for field in EVENT_TYPE_FIELD_CANDIDATES:
        if context.get(field):
            return context[field]
    for field in EVENT_TYPE_FIELD_CANDIDATES:
        if event.get(field):
            return event[field]
    return event.get("type", "")


def _get_task_correlation(event: dict) -> Optional[str]:
    context = event.get("context") or {}
    return context.get("task_id") or event.get("task_id")


def _event_fingerprint(event: dict) -> str:
    event_id = event.get("event_id") or event.get("msg_id")
    task_id = _get_task_correlation(event)
    event_type = _get_event_type(event)
    raw = "|".join([event_id or "", task_id or "", event_type])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


NEXT_ACTION_FIELDS = ("next_action", "follow_up", "followup")


def _explicit_next_action(event: dict) -> Optional[dict]:
    """Return the event's declared follow-up action, or None (fail-closed).

    Only an explicitly declared next action authorizes promotion of a
    completed task into a new assignment; otherwise no generic follow-up is
    emitted.
    """
    context = event.get("context") or {}
    for field in NEXT_ACTION_FIELDS:
        spec = context.get(field)
        if isinstance(spec, dict) and spec.get("action"):
            return dict(spec)
    if context.get("action"):
        spec = {"action": context["action"], "params": context.get("params") or {}}
        if context.get("reply_to"):
            spec["reply_to"] = context["reply_to"]
        return spec
    return None


def read_continuation_events(messages_file: Optional[Path] = None) -> List[dict]:
    path = Path(messages_file) if messages_file else MESSAGES_FILE
    if not path.exists():
        return []
    events = []
    try:
        with path.open("r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if msg.get("type") == "continuation_event":
                    events.append(msg)
    except Exception:
        pass
    return events


class FactoryIntake:
    """Factory-side continuation consumer with durable, checkout-local state."""
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            self.repo_root = REPO_ROOT
            # Preserve the module-level injection seam used by existing tests/tools.
            self.messages_file = Path(MESSAGES_FILE)
            self.intake_state = Path(INTAKE_STATE)
        else:
            self.repo_root = Path(repo_root)
            self.messages_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"
            self.intake_state = self.repo_root / "state" / "factory_intake_state.json"
        self.state_dir = self.repo_root / "state"
        self.decisions_dir = self.repo_root / "state" / "intake_decisions"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_dir.mkdir(parents=True, exist_ok=True)
        self.state = _load_state(self.intake_state)
        self.consumed_ids = set(self.state.get("consumed_ids", []))
        self.decisions = list(self.state.get("decisions", []))

    def _paths(self):
        # Supports legacy __new__-constructed test instances while keeping runtime paths local.
        messages = getattr(self, "messages_file", None)
        state = getattr(self, "intake_state", None)
        if messages is None:
            messages = Path(getattr(self, "repo_root", REPO_ROOT)) / "ai" / "coordination" / "messages.jsonl"
        if state is None:
            state = Path(getattr(self, "repo_root", REPO_ROOT)) / "state" / "factory_intake_state.json"
        return Path(messages), Path(state)

    def _persist(self):
        _, state_path = self._paths()
        state = {"consumed_ids": sorted(self.consumed_ids)[-5000:], "decisions": self.decisions[-5000:]}
        _save_state(state, state_path)

    def intake_once(self) -> List[dict]:
        messages_path, _ = self._paths()
        decisions = []
        for event in read_continuation_events(messages_path):
            decision = self.process_event(event)
            if decision:
                decisions.append(decision)
        return decisions

    def process_event(self, event: dict):
        fp = _event_fingerprint(event)
        if not fp or fp in self.consumed_ids:
            return None
        self.consumed_ids.add(fp)
        event_type = _get_event_type(event)
        if event_type not in WAKE_EVENT_TYPES:
            self._persist()
            return None
        task_id = _get_task_correlation(event) or "uncorrelated"
        if not self._should_follow_up(event, task_id):
            reason = "no_explicit_next_action" if event_type == "task_completed" else None
            decision = {"fingerprint": fp, "event_id": event.get("event_id") or event.get("msg_id"), "event_type": event_type, "task_id": task_id, "assigned_msg_id": None, "reason": reason, "decided_at": datetime.now(timezone.utc).isoformat()}
            self.decisions.append(decision)
            self._persist()
            return decision
        assignment = self._emit_next_task(event, task_id)
        decision = {"fingerprint": fp, "event_id": event.get("event_id") or event.get("msg_id"), "event_type": event_type, "task_id": task_id, "assigned_msg_id": assignment["msg_id"], "decided_at": datetime.now(timezone.utc).isoformat()}
        self.decisions.append(decision)
        self._persist()
        return decision

    def _should_follow_up(self, event: dict, task_id: str) -> bool:
        if not task_id or task_id == "uncorrelated":
            return False
        event_type = _get_event_type(event)
        if event_type in {"security_boundary", "authorization_required", "test_failure", "blocked"}:
            return True
        if event_type == "task_completed":
            context = event.get("context") or {}
            next_action = context.get("next_action") or event.get("next_action")
            explicit = _explicit_next_action(event)
            if explicit is not None:
                return True
            return isinstance(next_action, str) and bool(next_action.strip())
        return False

    def _emit_next_task(self, event: dict, task_id: str) -> dict:
        messages_path, _ = self._paths()
        now = datetime.now(timezone.utc)
        suffix = _event_fingerprint(event)[:12]
        source_id = event.get("event_id") or event.get("msg_id") or suffix
        next_task_id = f"intake-{now.strftime('%Y%m%d%H%M%S')}-{suffix}"
        msg_id = f"factory-intake-{suffix}"
        next_action = _explicit_next_action(event) or {}
        action = next_action.get("action") or "system_status"
        params = next_action.get("params") or {}
        reply_to = next_action.get("reply_to") or (event.get("context") or {}).get("reply_to") or source_id
        assignment = {"from": "factory", "to": TARGET_PARTY, "type": "task_assignment", "message": f"Factory continuation intake: follow-up on {task_id[:12]}... ({_get_event_type(event)})", "msg_id": msg_id, "timestamp": now.isoformat(), "context": {"task_id": next_task_id, "action": action, "params": params, "reply_to": reply_to, "source_event": source_id, "source_event_type": _get_event_type(event), "source_task_id": task_id}}
        try:
            messages_path.parent.mkdir(parents=True, exist_ok=True)
            with messages_path.open("a") as f:
                f.write(json.dumps(assignment) + "\n")
        except Exception as exc:
            log.error("Failed to write assignment: %s", exc)
        return assignment

    def pending_wake_events(self) -> List[dict]:
        messages_path, _ = self._paths()
        pending = []
        for event in read_continuation_events(messages_path):
            fp = _event_fingerprint(event)
            if fp not in self.consumed_ids and _get_event_type(event) in WAKE_EVENT_TYPES:
                pending.append(event)
        return pending


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Factory-side continuation intake")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("process")
    sub.add_parser("pending")
    sub.add_parser("status")
    args = parser.parse_args()
    intake = FactoryIntake()
    if args.cmd == "process":
        decisions = intake.intake_once()
        print(f"Processed {len(decisions)} events -> {len(decisions)} decisions")
    elif args.cmd == "pending":
        print(f"{len(intake.pending_wake_events())} pending wake events")
    elif args.cmd == "status":
        print(json.dumps({"consumed": len(intake.consumed_ids), "decisions": len(intake.decisions), "pending_wake": len(intake.pending_wake_events())}, indent=2))
    else:
        parser.print_help()
