#!/usr/bin/env python3
"""
Event Router — continuous dispatcher/party-routing layer.

Consumes events from the coordination bus (messages.jsonl), deduplicates,
routes to the appropriate party based on event type and capabilities,
and manages the external trigger boundary.

Lifecycle:
  Event arrives on messages.jsonl
  → Router reads it, deduplicates by event_id/msg_id
  → Determines which party should handle it
  → Writes a task to that party's inbound queue
  → If party is external (factory/chatgpt), signals a trigger request
  → Party processes and writes result back to messages.jsonl
  → Router picks up result, loops

Key constraints:
  - Fail-closed: if transport unavailable, events queue locally
  - No secrets in events
  - No direct main pushes
  - Dedup by event_id
  - External-trigger adapter: signals need for external wake without faking it
"""

import json
import os
import sys
import hashlib
import logging
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [EventRouter] %(message)s')
log = logging.getLogger("EventRouter")

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = REPO_ROOT / "state"
MESSAGES_FILE = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
ROUTER_STATE = STATE_DIR / "router_state.json"
TRIGGER_REQUESTS = STATE_DIR / "trigger_requests.jsonl"
INBOUND_DIR = STATE_DIR / "inbound"


# ── Event classification ──

WAKE_EVENT_TYPES = frozenset({
    "task_result", "continuation_event", "new_commit", "test_failure",
    "blocked", "authorization_required", "security_boundary",
    "blocker", "approval_needed", "task_completed",
})

HEARTBEAT_EVENT_TYPES = frozenset({
    "heartbeat", "state_check", "system_status",
})

# Party routing: which event types each party can handle
PARTY_CAPABILITIES = {
    "anyclaw": {
        "can_handle": {"task_assignment", "health_check", "system_status", "read_file_fact"},
        "produces": {"task_result", "continuation_event"},
        "transport": "inbox_file",  # reads from ai/tasks/inbox.jsonl
        "wake_capable": False,  # AnyClaw polls, doesn't need waking
    },
    "factory": {
        "can_handle": {"task_result", "continuation_event", "blocker", "approval_needed"},
        "produces": {"task_assignment"},
        "transport": "github_issue",  # signals via GitHub issue comment
        "wake_capable": True,  # needs external trigger (human opens ChatGPT)
    },
    "operator": {
        "can_handle": {"trade_alert", "approval_needed", "system_status", "error"},
        "produces": {},
        "transport": "telegram",
        "wake_capable": False,
    },
    "telegram": {
        "can_handle": {},
        "produces": {},
        "transport": "telegram",
        "wake_capable": False,
    },
    "openclaw": {
        "can_handle": {"task_assignment", "health_check", "system_status", "read_file_fact"},
        "produces": {"task_result", "continuation_event"},
        "transport": "file",
        "wake_capable": False,
    },
    "grok": {
        "can_handle": {"query", "task_assignment"},
        "produces": {"query_result", "task_result"},
        "transport": "file",
        "wake_capable": False,
    },
    "system_internal": {
        "can_handle": {"*"},
        "produces": {"system_status", "health_check"},
        "transport": "file",
        "wake_capable": False,
    },
}


class EventRouter:
    """Routes events between parties on the coordination bus."""

    def __init__(self, repo_root=None):
        self.repo_root = Path(repo_root) if repo_root else REPO_ROOT
        self.state_dir = self.repo_root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.messages_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"
        self.router_state = self.state_dir / "router_state.json"
        self.trigger_requests = self.state_dir / "trigger_requests.jsonl"
        self.inbound_dir = self.state_dir / "inbound"
        self.inbound_dir.mkdir(parents=True, exist_ok=True)

        self.processed_ids = self._load_processed()
        self.cursor = 0  # byte offset into messages.jsonl
        self._load_cursor()

    def _load_processed(self) -> Set[str]:
        path = STATE_DIR / "router_processed_ids.json"
        if path.exists():
            try:
                return set(json.loads(path.read_text()))
            except Exception:
                pass
        return set()

    def _save_processed(self):
        path = STATE_DIR / "router_processed_ids.json"
        # Keep only last 1000 IDs to prevent unbounded growth
        ids = sorted(self.processed_ids)
        if len(ids) > 1000:
            ids = ids[-1000:]
            self.processed_ids = set(ids)
        path.write_text(json.dumps(ids))

    def _load_cursor(self):
        if self.router_state.exists():
            try:
                state = json.loads(self.router_state.read_text())
                self.cursor = state.get("cursor", 0)
            except Exception:
                pass

    def _save_cursor(self):
        self.router_state.write_text(json.dumps({"cursor": self.cursor}))

    def read_new_messages(self) -> List[Dict]:
        """Read new messages from messages.jsonl since last cursor."""
        if not self.messages_file.exists():
            return []

        messages = []
        try:
            with open(self.messages_file, "r") as f:
                f.seek(self.cursor)
                while True:
                    line = f.readline()
                    if not line:
                        break
                    if line.strip():
                        try:
                            msg = json.loads(line)
                            msg_id = msg.get("msg_id", "")
                            if msg_id and msg_id not in self.processed_ids:
                                messages.append(msg)
                                self.processed_ids.add(msg_id)
                        except json.JSONDecodeError:
                            pass
                self.cursor = f.tell()
        except Exception as e:
            log.error(f"Error reading messages: {e}")

        return messages

    def classify_event(self, msg: Dict) -> str:
        """Classify a message as wake, heartbeat, or ignore."""
        msg_type = msg.get("type", "")
        context = msg.get("context", {})

        # Check if it's a continuation event with explicit is_wake
        if msg_type == "continuation_event" and "is_wake" in context:
            return "wake" if context["is_wake"] else "heartbeat"

        if msg_type in WAKE_EVENT_TYPES:
            return "wake"
        if msg_type in HEARTBEAT_EVENT_TYPES:
            return "heartbeat"
        return "ignore"

    def determine_handler(self, msg: Dict) -> Optional[str]:
        """Determine which party should handle this message."""
        msg_type = msg.get("type", "")
        sender = msg.get("from", "")
        context = msg.get("context", {})
        event_type = context.get("event_type", msg_type)
        handler_party = context.get("target_party", msg.get("to", ""))

        # Task results from AnyClaw → route to Factory for next task
        if sender == "anyclaw" and msg_type in ("task_result", "continuation_event"):
            return "factory"

        # Task assignments from Factory → route to AnyClaw
        if sender == "factory" and msg_type == "task_assignment":
            return "anyclaw"

        # Approval needed → route to operator
        if event_type in ("approval_needed", "blocked"):
            if sender == "anyclaw":
                return "operator"
            return "factory"

        # System events → route to system_internal
        if msg_type in ("system_status", "health_check"):
            return "system_internal"

        # Task results from openclaw or grok → route to factory
        if sender in ("openclaw", "grok") and msg_type in ("task_result", "query_result"):
            return "factory"

        # Task assignments from factory or anyclaw to openclaw/grok
        if msg_type == "task_assignment" and handler_party in ("openclaw", "grok"):
            return handler_party

        # Continuation events from AnyClaw → route to Factory
        if sender == "anyclaw" and event_type in WAKE_EVENT_TYPES:
            return "factory"

        return None

    def route_event(self, msg: Dict) -> Optional[Dict]:
        """Route a single event to the appropriate party. Returns the routing record."""
        handler = self.determine_handler(msg)
        if not handler:
            log.info(f"No handler for message {msg.get('msg_id', '?')[:8]}...")
            return None

        classification = self.classify_event(msg)
        msg_id = msg.get("msg_id", "")
        msg_type = msg.get("type", "")

        # Build routing record
        record = {
            "event_id": msg_id,
            "from": msg.get("from", "unknown"),
            "to": handler,
            "event_type": msg_type,
            "classification": classification,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlated_to": msg.get("context", {}).get("task_id") or msg.get("context", {}).get("correlation_id"),
            "routed": True,
        }

        # Write to handler's inbound queue
        inbound_file = self.inbound_dir / f"{handler}.jsonl"
        try:
            with open(inbound_file, "a") as f:
                f.write(json.dumps(record) + "\n")
            log.info(f"Routed {msg_type} from {msg.get('from', '?')} → {handler} ({classification})")
        except Exception as e:
            log.error(f"Failed to route to {handler}: {e}")
            record["routed"] = False
            record["error"] = str(e)

        # If handler needs external trigger, create trigger request
        handler_cap = PARTY_CAPABILITIES.get(handler, {})
        if handler_cap.get("wake_capable") and classification == "wake":
            self._create_trigger_request(msg, handler, record)

        return record

    def _create_trigger_request(self, msg: Dict, handler: str, record: Dict):
        """Create an external trigger request for parties that need human/automation wake."""
        request = {
            "request_id": record["event_id"],
            "target_party": handler,
            "event_type": record["event_type"],
            "summary": msg.get("message", "")[:200],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "context": {
                "from": msg.get("from"),
                "task_id": msg.get("context", {}).get("task_id"),
                "commit": msg.get("context", {}).get("commit"),
            },
        }

        # Dedup trigger requests
        existing = set()
        if self.trigger_requests.exists():
            try:
                with open(self.trigger_requests, "r") as f:
                    for line in f:
                        if line.strip():
                            r = json.loads(line)
                            existing.add(r.get("request_id", ""))
            except Exception:
                pass

        if request["request_id"] not in existing:
            try:
                with open(self.trigger_requests, "a") as f:
                    f.write(json.dumps(request) + "\n")
                log.info(f"Trigger request created for {handler}: {record['event_type']}")
            except Exception as e:
                log.error(f"Failed to create trigger request: {e}")

    def process_once(self) -> int:
        """Process all new messages in one pass. Returns count routed."""
        messages = self.read_new_messages()
        routed = 0

        for msg in messages:
            record = self.route_event(msg)
            if record and record.get("routed"):
                routed += 1

        if routed:
            self._save_processed()
            self._save_cursor()

        return routed

    def get_pending_triggers(self) -> List[Dict]:
        """Get unprocessed trigger requests."""
        if not self.trigger_requests.exists():
            return []
        requests = []
        handled = set()
        # Check which triggers have been acted on
        act_file = STATE_DIR / "trigger_acted.jsonl"
        if act_file.exists():
            try:
                with open(act_file, "r") as f:
                    for line in f:
                        if line.strip():
                            handled.add(json.loads(line).get("request_id", ""))
            except Exception:
                pass

        with open(self.trigger_requests, "r") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r.get("request_id") not in handled:
                        requests.append(r)
        return requests

    def get_status(self) -> Dict:
        """Get router status summary."""
        return {
            "cursor": self.cursor,
            "processed_count": len(self.processed_ids),
            "pending_triggers": len(self.get_pending_triggers()),
            "messages_file_exists": self.messages_file.exists(),
            "messages_file_size": self.messages_file.stat().st_size if self.messages_file.exists() else 0,
        }


# ── External Trigger Adapter ──
# The "final hop" — signals that an external party needs to be woken.
# Cannot actually trigger ChatGPT; emits a signal for human/automation.

def external_trigger_adapter():
    """Check for pending triggers and emit signals (stdout/file)."""
    router = EventRouter()
    pending = router.get_pending_triggers()

    if not pending:
        return {"status": "no_pending_triggers"}

    signals = []
    for trigger in pending:
        signal = {
            "signal_type": "external_wake_needed",
            "target": trigger["target_party"],
            "event_type": trigger["event_type"],
            "summary": trigger["summary"],
            "instruction": f"Open {trigger['target_party']} and inspect issue #281 for context",
        }
        signals.append(signal)

        # Also write a human-readable trigger file
        trigger_file = STATE_DIR / f"trigger_{trigger['request_id'][:8]}.txt"
        try:
            trigger_file.write_text(
                f"TRIGGER: {trigger['target_party']}\n"
                f"Event: {trigger['event_type']}\n"
                f"Summary: {trigger['summary']}\n"
                f"Action: Open ChatGPT and check GitHub issue #281\n"
            )
        except Exception:
            pass

    return {"status": "triggers_pending", "count": len(signals), "signals": signals}


# ── Main ──

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Event Router — dispatches events between parties")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("process", help="Process new messages once")
    loop_p = sub.add_parser("loop", help="Process continuously")
    loop_p.add_argument("--interval", type=int, default=10)
    sub.add_parser("status", help="Show router status")
    sub.add_parser("triggers", help="Show pending trigger requests")

    args = parser.parse_args()
    router = EventRouter()

    if args.cmd == "process":
        count = router.process_once()
        print(f"Routed {count} events")
    elif args.cmd == "loop":
        log.info("Event router started (continuous mode)")
        while True:
            try:
                count = router.process_once()
                if count:
                    log.info(f"Routed {count} events")
            except Exception as e:
                log.error(f"Error: {e}")
            time.sleep(args.interval)
    elif args.cmd == "status":
        status = router.get_status()
        print(json.dumps(status, indent=2))
    elif args.cmd == "triggers":
        triggers = router.get_pending_triggers()
        for t in triggers:
            print(f"[{t['event_type']}] → {t['target_party']}: {t['summary'][:100]}")
        if not triggers:
            print("No pending triggers")
    else:
        parser.print_help()
