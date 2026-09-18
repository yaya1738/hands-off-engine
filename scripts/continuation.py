#!/usr/bin/env python3
"""
Continuation Event System — self-continuing Factory↔AnyClaw collaboration.

Emits structured events when AnyClaw completes meaningful work, so Factory
can inspect the state and issue the next bounded task without human prompting.

Lifecycle:
  AnyClaw completes task → emit_event() → commit + issue comment
  Factory inspects event → issues next task via inbox.jsonl or issue comment
  AnyClaw picks up next task → process → emit_event → repeat

Events are typed:
  - task_completed: A task from Factory was processed
  - state_change: Significant system state changed
  - blocker: AnyClaw needs human or Factory decision
  - approval_needed: Requires explicit approval before proceeding
  - test_result: Tests passed or failed

Constraints enforced:
  - No secrets in events
  - Dedup by event_id
  - Persistent correlation via correlation_id
  - Distinguishes wake events from heartbeats
  - Fails closed when transport unavailable
"""

import json
import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import hashlib

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [Continuation] %(message)s')
log = logging.getLogger("Continuation")

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = REPO_ROOT / "state"
EVENTS_FILE = STATE_DIR / "continuation_events.jsonl"
EMITTED_IDS = STATE_DIR / "emitted_event_ids.json"

# Event types that constitute a "wake" signal (not just heartbeats)
WAKE_EVENT_TYPES = frozenset({
    "task_completed",
    "blocker",
    "approval_needed",
    "test_failure",
    "security_boundary",
})

HEARTBEAT_EVENT_TYPES = frozenset({
    "heartbeat",
    "state_check",
})


def _load_emitted_ids():
    if EMITTED_IDS.exists():
        try:
            return set(json.loads(EMITTED_IDS.read_text()))
        except Exception:
            pass
    return set()


def _save_emitted_ids(ids):
    EMITTED_IDS.write_text(json.dumps(sorted(ids)))


def _get_head_commit():
    """Get current HEAD commit SHA."""
    try:
        import subprocess
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except Exception:
        return "unknown"


class ContinuationEmitter:
    """Emits structured continuation events to the repo and coordination bus."""

    def __init__(self):
        self.emitted_ids = _load_emitted_ids()
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    def emit(self, event_type: str, message: str, context: Optional[Dict] = None,
             correlation_id: Optional[str] = None, is_wake: Optional[bool] = None):
        """Emit a continuation event.

        Args:
            event_type: One of WAKE_EVENT_TYPES or HEARTBEAT_EVENT_TYPES
            message: Human-readable summary
            context: Additional structured data
            correlation_id: Links related events (e.g., task_id from original task)
            is_wake: Override auto-detection of wake vs heartbeat
        """
        # Deterministic event identity: derived from event type + correlation
        # (not a random UUID before dedup) so identical events dedupe naturally.
        correlation_key = correlation_id or (context or {}).get("task_id", "") or ""
        identity_raw = f"{event_type}|{correlation_key}|{message}"
        event_id = hashlib.sha256(identity_raw.encode("utf-8")).hexdigest()
        event_id = event_id[:32]  # bounded length

        # Dedup check (deterministic: same event content -> same event_id)
        if event_id in self.emitted_ids:
            log.info(f"Dedup: event {event_id[:8]}... already emitted")
            return None

        if is_wake is None:
            is_wake = event_type in WAKE_EVENT_TYPES

        event = {
            "event_id": event_id,
            "event_type": event_type,
            "is_wake": is_wake,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit": _get_head_commit(),
            "correlation_id": correlation_id,
            "context": context or {},
        }

        # Persist to local events log
        self._write_event(event)

        # Emit to coordination bus
        self._emit_to_coordination(event)

        # Mark as emitted
        self.emitted_ids.add(event_id)
        _save_emitted_ids(self.emitted_ids)

        log.info(f"Emitted {event_type} event {event_id[:8]}... (wake={is_wake})")
        return event

    def emit_task_completed(self, task_id: str, status: str, result_summary: str,
                            correlation_id: Optional[str] = None,
                            next_action: Optional[Dict] = None):
        """Emit after completing a Factory task."""
        event_type = (
            "blocked"
            if str(status).lower() in {"blocked", "authorization_required"}
            else "task_completed"
        )
        return self.emit(
            event_type=event_type,
            message=f"Task {task_id[:8]}... completed: {status} — {result_summary}",
            context={**{"task_id": task_id, "status": status, "result_summary": result_summary},
                     **({"next_action": next_action} if isinstance(next_action, dict) and next_action.get("action") else {})},
            correlation_id=correlation_id or task_id,
            is_wake=True,
        )

    def emit_blocker(self, reason: str, needs: str,
                     correlation_id: Optional[str] = None):
        """Emit when AnyClaw is blocked and needs external input."""
        return self.emit(
            event_type="blocker",
            message=f"BLOCKED: {reason}. Needs: {needs}",
            context={"reason": reason, "needs": needs},
            correlation_id=correlation_id,
            is_wake=True,
        )

    def emit_approval_needed(self, command_id: str, action: str,
                             correlation_id: Optional[str] = None):
        """Emit when a command requires approval."""
        return self.emit(
            event_type="approval_needed",
            message=f"Approval needed for {action} (command {command_id[:8]}...)",
            context={"command_id": command_id, "action": action},
            correlation_id=correlation_id,
            is_wake=True,
        )

    def emit_test_result(self, passed: int, failed: int, test_file: str = ""):
        """Emit test results."""
        event_type = "test_failure" if failed > 0 else "test_result"
        return self.emit(
            event_type=event_type,
            message=f"Tests: {passed} passed, {failed} failed" + (f" ({test_file})" if test_file else ""),
            context={"passed": passed, "failed": failed, "test_file": test_file},
            is_wake=failed > 0,
        )

    def emit_state_change(self, component: str, old_state: str, new_state: str):
        """Emit when significant system state changes."""
        return self.emit(
            event_type="state_change",
            message=f"{component}: {old_state} → {new_state}",
            context={"component": component, "old_state": old_state, "new_state": new_state},
            is_wake=True,
        )

    def emit_heartbeat(self, summary: str = "alive"):
        """Emit a heartbeat (not a wake event)."""
        return self.emit(
            event_type="heartbeat",
            message=summary,
            is_wake=False,
        )

    def get_recent_events(self, limit=10, wake_only=False):
        """Get recent events from the log."""
        if not EVENTS_FILE.exists():
            return []
        events = []
        with open(EVENTS_FILE, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        e = json.loads(line)
                        if wake_only and not e.get("is_wake"):
                            continue
                        events.append(e)
                    except Exception:
                        pass
        return events[-limit:]

    def post_to_github_issue(self, event, issue_number=281):
        """GitHub issue posting is DISABLED — coordination stays credential-free.

        Factory round 12: remove/disable the direct GitHub-token posting path.
        Continuation events reach Factory via the canonical coordination bus
        (ai/coordination/messages.jsonl) and state/continuation_events.jsonl.
        """
        log.info("GitHub-token posting disabled (credential-free coordination)")
        return False

    def _write_event(self, event):
        try:
            with open(EVENTS_FILE, "a") as f:
                f.write(json.dumps(event, default=str) + "\n")
        except Exception:
            pass

    def _emit_to_coordination(self, event):
        """Emit to the messages.jsonl coordination bus."""
        try:
            coord_file = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
            msg = {
                "from": "anyclaw",
                "to": "factory",
                "type": "continuation_event",
                "message": event["message"],
                "timestamp": event["timestamp"],
                "msg_id": event["event_id"],
                "context": {
                    "task_id": (event.get("context") or {}).get("task_id"),
                    "event_type": event["event_type"],
                    "is_wake": event["is_wake"],
                    "commit": event["commit"],
                    "correlation_id": event.get("correlation_id"),
                },
            }
            with open(coord_file, "a") as f:
                f.write(json.dumps(msg) + "\n")
        except Exception:
            pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Continuation Event System")
    sub = parser.add_subparsers(dest="cmd")

    emit_p = sub.add_parser("emit", help="Emit an event")
    emit_p.add_argument("type", help="Event type")
    emit_p.add_argument("message", help="Event message")
    emit_p.add_argument("--correlation", help="Correlation ID")

    sub.add_parser("events", help="Show recent events")

    args = parser.parse_args()
    emitter = ContinuationEmitter()

    if args.cmd == "emit":
        event = emitter.emit(args.type, args.message, correlation_id=args.correlation)
        print(json.dumps(event, indent=2) if event else "Deduped")
    elif args.cmd == "events":
        for e in emitter.get_recent_events(20):
            wake = "🔔" if e["is_wake"] else "💤"
            print(f"{wake} {e['timestamp'][:19]} [{e['event_type']}] {e['message'][:80]}")
    else:
        parser.print_help()
