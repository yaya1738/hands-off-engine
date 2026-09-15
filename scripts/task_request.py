#!/usr/bin/env python3
"""Task Request — AnyClaw → Factory ingress adapter.

Closes the bidirectional gap: AnyClaw can now proactively request work
from Factory rather than only receiving task_assignments.

The canonical transport and source of truth remain
`ai/coordination/messages.jsonl`; this adapter writes type=task_request
messages to it. Local state is a bounded derived cache (last 100 sent)
and is never required to reconstruct or route a request.

Request types:
- work_request: AnyClaw asks Factory for a new task
- question: AnyClaw asks Factory a bounded question
- status_probe: AnyClaw asks Factory about the system state

All filesystem paths derive from the supplied checkout root; module
functions are thin wrappers over a default-root adapter for CLI use.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent

ALLOWED_TYPES = {"work_request", "question", "status_probe"}


def _request_id(request_type, message):
    raw = f"{request_type}|{message}|{datetime.now(timezone.utc).isoformat()}"
    return "req-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


class TaskRequest:
    """Checkout-local AnyClaw → Factory ingress adapter."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = Path(repo_root) if repo_root else ROOT
        self.bus = self.repo_root / "ai" / "coordination" / "messages.jsonl"
        self.state_file = self.repo_root / "state" / "task_request_state.json"

    def load_state(self) -> dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception:
                pass
        return {"sent": [], "pending": []}

    def save_state(self, state: dict):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(state, indent=2) + "\n")

    def send(self, request_type: str, message: str, params=None) -> str:
        """Send a bounded request from AnyClaw to Factory via the canonical bus."""
        if request_type not in ALLOWED_TYPES:
            raise ValueError(f"Invalid request type: {request_type}. Allowed: {sorted(ALLOWED_TYPES)}")

        rid = _request_id(request_type, message)
        ts = datetime.now(timezone.utc).isoformat()

        bus_msg = {
            "from": "anyclaw",
            "to": "factory",
            "type": "task_request",
            "message": message,
            "msg_id": rid,
            "timestamp": ts,
            "priority": 7,
            "context": {
                "request_type": request_type,
                "params": params or {},
            },
        }

        self.bus.parent.mkdir(parents=True, exist_ok=True)
        with self.bus.open("a") as f:
            f.write(json.dumps(bus_msg) + "\n")

        state = self.load_state()
        state["sent"].append({
            "id": rid,
            "type": request_type,
            "message": message,
            "timestamp": ts,
        })
        state["sent"] = state["sent"][-100:]
        self.save_state(state)
        return rid

    def work(self, message: str = "Ready for new tasks") -> str:
        return self.send("work_request", message)

    def question(self, question: str, context=None) -> str:
        return self.send("question", question, params=context or {})

    def status(self) -> str:
        return self.send("status_probe", "Requesting system status update")


# ── CLI convenience wrappers (default checkout root) ──

def send_request(request_type, message, params=None):
    return TaskRequest().send(request_type, message, params)


def request_work(message="Ready for new tasks"):
    return TaskRequest().work(message)


def ask_question(question, context=None):
    return TaskRequest().question(question, context)


def probe_status():
    return TaskRequest().status()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 task_request.py work     — request new work")
        print("  python3 task_request.py question  — ask a question")
        print("  python3 task_request.py status    — probe status")
    elif sys.argv[1] == "work":
        msg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Ready for new tasks"
        request_work(msg)
    elif sys.argv[1] == "question":
        msg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "What is the next priority?"
        ask_question(msg)
    elif sys.argv[1] == "status":
        probe_status()
