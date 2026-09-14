#!/usr/bin/env python3
"""Task Request — AnyClaw → Factory request channel.

Closes the bidirectional gap: AnyClaw can now proactively request work
from Factory rather than only receiving task_assignments. This is the
missing seam identified in the autonomous loop audit.

Request types:
- work_request: AnyClaw asks Factory for a new task
- question: AnyClaw asks Factory a bounded question
- status_probe: AnyClaw asks Factory about the system state

Requests are posted to the canonical bus as type=task_request.
Factory can respond with task_assignment through the existing intake path.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"
REQUEST_STATE = ROOT / "state/task_request_state.json"

ALLOWED_TYPES = {"work_request", "question", "status_probe"}


def request_id(request_type, message):
    raw = f"{request_type}|{message}|{datetime.now(timezone.utc).isoformat()}"
    return "req-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_state():
    if REQUEST_STATE.exists():
        try:
            return json.loads(REQUEST_STATE.read_text())
        except Exception:
            pass
    return {"sent": [], "pending": []}


def save_state(state):
    REQUEST_STATE.parent.mkdir(parents=True, exist_ok=True)
    REQUEST_STATE.write_text(json.dumps(state, indent=2) + "\n")


def send_request(request_type, message, params=None):
    """Send a bounded request from AnyClaw to Factory via the canonical bus."""
    if request_type not in ALLOWED_TYPES:
        raise ValueError(f"Invalid request type: {request_type}. Allowed: {ALLOWED_TYPES}")
    
    rid = request_id(request_type, message)
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
    
    with open(BUS, "a") as f:
        f.write(json.dumps(bus_msg) + "\n")
    
    state = load_state()
    state["sent"].append({
        "id": rid,
        "type": request_type,
        "message": message,
        "timestamp": ts,
    })
    # Keep last 100
    state["sent"] = state["sent"][-100:]
    save_state(state)
    
    print(f"Request sent: {rid} ({request_type})")
    print(f"  Message: {message[:100]}")
    return rid


def request_work(message="Ready for new tasks"):
    """AnyClaw asks Factory for work."""
    return send_request("work_request", message)


def ask_question(question, context=None):
    """AnyClaw asks Factory a bounded question."""
    return send_request("question", question, params=context or {})


def probe_status():
    """AnyClaw asks Factory for system status."""
    return send_request("status_probe", "Requesting system status update")


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
