#!/usr/bin/env python3
"""
Factory-side continuation intake.

Consumes `continuation_event` entries from the canonical coordination bus
(ai/coordination/messages.jsonl), validates/correlates event_id/msg_id and
task_id, durably deduplicates across restart, filters to wake-worthy events
only, and produces exactly one bounded next `task_assignment` addressed to
anyclaw through the same canonical bus.

Design constraints (per Factory round 12):
- No second bus, no credentials, no live execution, no direct main push
- Durable consumption/decision state so restart cannot fan out duplicates
- Deterministic correlation: event identity derived from event data, not UUID
"""

import json
import sys
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [FactoryIntake] %(message)s')
log = logging.getLogger("FactoryIntake")

REPO_ROOT = Path(__file__).resolve().parent.parent
MESSAGES_FILE = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
INTAKE_STATE = REPO_ROOT / "state" / "factory_intake_state.json"
DECISION_DIR = REPO_ROOT / "state" / "intake_decisions"

# Wake-worthy event types (only these trigger a next-task decision)
WAKE_EVENT_TYPES = frozenset({
    "task_completed",
    "blocked",
    "authorization_required",
    "security_boundary",
    "test_failure",
})

# The only action produced by this intake is a bounded task_assignment to anyclaw
TARGET_PARTY = "anyclaw"

# Canonical envelope requirement: acceptable in-message event_type fields
EVENT_TYPE_FIELD_CANDIDATES = ("event_type", "type")


def _load_state() -> dict:
    if INTAKE_STATE.exists():
        try:
            return json.loads(INTAKE_STATE.read_text())
        except Exception:
            pass
    return {"consumed_ids": [], "decisions": []}


def _save_state(state: dict):
    INTAKE_STATE.write_text(json.dumps(state, indent=2) + "\n")


def _get_event_type(event: dict) -> str:
    """Extract the effective event type from a bus message.

    Bus messages have event_type inside context (from continuation emitter):
    {"type": "continuation_event", "context": {"event_type": "task_completed", ...}}
    Also checks top-level fields for flat events.
    """
    # Check context first (standard bus envelope from continuation emitter)
    context = event.get("context") or {}
    for field in EVENT_TYPE_FIELD_CANDIDATES:
        val = context.get(field)
        if val:
            return val
    # Fall back to top-level fields
    for field in EVENT_TYPE_FIELD_CANDIDATES:
        val = event.get(field)
        if val:
            return val
    # Fall back to message-level type
    return event.get("type", "")


def _get_task_correlation(event: dict) -> Optional[str]:
    """Extract task_id correlation from the bus message (context or top-level)."""
    context = event.get("context") or {}
    return context.get("task_id") or event.get("task_id")


def _event_fingerprint(event: dict) -> str:
    """Deterministic identity from event data (event_id preferred, else msg_id + task correlation)."""
    event_id = event.get("event_id") or event.get("msg_id")
    task_id = _get_task_correlation(event)
    event_type = _get_event_type(event)
    raw = "|".join([event_id or "", task_id or "", event_type])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def read_continuation_events() -> List[dict]:
    """Read all continuation_event entries from the canonical bus."""
    if not MESSAGES_FILE.exists():
        return []
    events = []
    try:
        with open(MESSAGES_FILE, "r") as f:
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
    """Factory-side continuation consumer: dedup → filter → decide → emit exactly one task."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = Path(repo_root) if repo_root else REPO_ROOT
        self.state_dir = self.repo_root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_dir = DECISION_DIR
        self.decisions_dir.mkdir(parents=True, exist_ok=True)
        self.state = _load_state()
        self.consumed_ids = set(self.state.get("consumed_ids", []))
        self.decisions = list(self.state.get("decisions", []))

    # ── durable consumption state ──

    def _persist(self):
        state = {
            "consumed_ids": sorted(self.consumed_ids)[-5000:],
            "decisions": self.decisions[-5000:],
        }
        INTAKE_STATE.write_text(json.dumps(state, indent=2) + "\n")

    # ── intake pipeline ──

    def intake_once(self) -> List[dict]:
        """Process all un-consumed continuation events. Returns decision records."""
        events = read_continuation_events()
        decisions = []
        for event in events:
            decision = self.process_event(event)
            if decision:
                decisions.append(decision)
        return decisions

    def process_event(self, event: dict) -> Optional[dict]:
        """Process one bus message. Returns a decision record or None if not actionable.

        Pipeline: validate envelope → dedup by fingerprint → wake-only filter
        → correlate task_id → emit exactly one task_assignment.
        """
        # 1. Envelope validation
        fp = _event_fingerprint(event)
        if not fp:
            log.warning("Rejected event: no usable identity")
            return None

        # 2. Durable dedup across restart
        if fp in self.consumed_ids:
            log.info(f"Dedup: event fingerprint {fp[:12]}... already consumed")
            return None
        self.consumed_ids.add(fp)

        # 3. Wake-only filter
        event_type = _get_event_type(event)
        if event_type not in WAKE_EVENT_TYPES:
            log.info(f"Ignoring non-wake event type: {event_type}")
            self._persist()
            return None

        # 4. Correlation
        task_id = _get_task_correlation(event)
        if not task_id:
            task_id = "uncorrelated"

        # 5. Exactly one bounded next task_assignment
        assignment = self._emit_next_task(event, task_id)

        decision = {
            "fingerprint": fp,
            "event_id": event.get("event_id") or event.get("msg_id"),
            "event_type": event_type,
            "task_id": task_id,
            "assigned_msg_id": assignment["msg_id"],
            "decided_at": datetime.now(timezone.utc).isoformat(),
        }
        self.decisions.append(decision)
        self._persist()
        log.info(f"Decided: {event_type} (task={task_id}) -> emitted {assignment['msg_id']}")
        return decision

    # ── exactly-one bounded next task ──

    def _emit_next_task(self, event: dict, task_id: str) -> dict:
        """Emit exactly one bounded task_assignment to anyclaw on the canonical bus."""
        next_task_id = f"intake-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        msg_id = f"factory-intake-{_event_fingerprint(event)[:12]}"

        assignment = {
            "from": "factory",
            "to": TARGET_PARTY,
            "type": "task_assignment",
            "message": f"Factory continuation intake: follow-up on {task_id[:12]}... ({_get_event_type(event)})",
            "msg_id": msg_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": {
                "task_id": next_task_id,
                "action": "system_status",
                "params": {},
                "reply_to": "281",
                "source_event": event.get("event_id") or event.get("msg_id"),
                "source_event_type": _get_event_type(event),
            },
        }
        try:
            out_path = self.repo_root / "ai" / "coordination" / "messages.jsonl"
            with open(out_path, "a") as f:
                f.write(json.dumps(assignment) + "\n")
        except Exception as e:
            log.error(f"Failed to write assignment: {e}")
        return assignment

    def pending_wake_events(self) -> List[dict]:
        """Return wake-worthy events not yet consumed (for Factory-side visibility)."""
        events = read_continuation_events()
        pending = []
        for event in events:
            fp = _event_fingerprint(event)
            if fp in self.consumed_ids:
                continue
            if _get_event_type(event) in WAKE_EVENT_TYPES:
                pending.append(event)
        return pending


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Factory-side continuation intake")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("process", help="Process all pending continuation events")
    sub.add_parser("pending", help="List pending wake-worthy events")
    sub.add_parser("status", help="Show intake state summary")

    args = parser.parse_args()
    intake = FactoryIntake()

    if args.cmd == "process":
        decisions = intake.intake_once()
        print(f"Processed {len(decisions)} events -> {len(decisions)} decisions")
        for d in decisions:
            print(f"  {d['event_type']} (task={d['task_id'][:16]}...) -> {d['assigned_msg_id']}")
    elif args.cmd == "pending":
        pending = intake.pending_wake_events()
        print(f"{len(pending)} pending wake events")
        for e in pending:
            print(f"  [{_get_event_type(e)}] {e.get('message', '')[:80]}")
    elif args.cmd == "status":
        print(json.dumps({
            "consumed": len(intake.consumed_ids),
            "decisions": len(intake.decisions),
            "pending_wake": len(intake.pending_wake_events()),
        }, indent=2))
    else:
        parser.print_help()
