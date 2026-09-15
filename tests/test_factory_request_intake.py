"""Focused tests for Factory-side request intake (admission gate).

Covers:
1. Sender validation (registered vs unknown vs unauthorized)
2. Request type validation (allowed vs invalid)
3. Correlation/dedup (same msg_id never admitted twice)
4. Contract validation (envelope, message length, msg_id presence)
5. Admission state persistence across restarts
6. No auto-dispatch (admitted requests stay queued, not forwarded)
7. Full happy-path round-trip
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.factory_request_intake as fri


def _make_intake():
    """Create an isolated RequestIntake with temp directories and parties."""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "state").mkdir()
    (tmp / "ai" / "coordination").mkdir(parents=True)

    # Write a minimal party registry with anyclaw authorized
    parties = {
        "anyclaw": {
            "id": "anyclaw",
            "name": "AnyClaw (Codex CLI)",
            "role": "agent",
            "trust_level": 9,
            "channels": ["file", "messages_jsonl"],
        },
        "operator": {
            "id": "operator",
            "name": "Yair Siegel",
            "role": "owner",
            "trust_level": 10,
            "channels": ["telegram"],
        },
        "chatgpt": {
            "id": "chatgpt",
            "name": "ChatGPT",
            "role": "agent",
            "trust_level": 7,
            "channels": ["webhook", "messages_jsonl"],
        },
        "system_internal": {
            "id": "system_internal",
            "name": "System",
            "role": "system",
            "trust_level": 5,
            "channels": ["file"],
        },
    }
    (tmp / "state" / "party_registry.json").write_text(json.dumps(parties))

    # Monkey-patch module-level paths
    orig_messages = fri.MESSAGES_FILE
    orig_state = fri.INTAKE_STATE
    orig_registry = fri.PARTY_REGISTRY

    fri.MESSAGES_FILE = tmp / "ai" / "coordination" / "messages.jsonl"
    fri.INTAKE_STATE = tmp / "state" / "request_intake_state.json"
    fri.PARTY_REGISTRY = tmp / "state" / "party_registry.json"

    intake = fri.RequestIntake.__new__(fri.RequestIntake)
    intake.repo_root = tmp
    intake.messages_file = fri.MESSAGES_FILE
    intake.state_file = fri.INTAKE_STATE
    intake.parties = json.loads((tmp / "state" / "party_registry.json").read_text())
    intake.state = {"admitted_ids": [], "rejected_ids": [], "admissions": [], "rejections": []}
    intake.admitted_ids = set()
    intake.rejected_ids = set()

    intake._tmp = tmp
    intake._orig = (orig_messages, orig_state, orig_registry)
    return intake


def _teardown(intake):
    fri.MESSAGES_FILE, fri.INTAKE_STATE, fri.PARTY_REGISTRY = intake._orig
    shutil.rmtree(intake._tmp)




def _seed_repo(tmp):
    """Seed a checkout-local repo root with party registry + empty bus."""
    (tmp / "state").mkdir(parents=True, exist_ok=True)
    (tmp / "ai" / "coordination").mkdir(parents=True, exist_ok=True)
    parties = {"anyclaw": {"id": "anyclaw", "name": "AnyClaw", "role": "agent", "trust_level": 9, "channels": ["messages_jsonl"]}}
    (tmp / "state" / "party_registry.json").write_text(json.dumps(parties))
    return tmp


def test_two_repo_roots_do_not_cross_contaminate():
    """RequestIntake instances are fully checkout-local (no module-global state)."""
    tmp_a = _seed_repo(Path(tempfile.mkdtemp()))
    tmp_b = _seed_repo(Path(tempfile.mkdtemp()))

    with open(tmp_a / "ai" / "coordination" / "messages.jsonl", "a") as f:
        f.write(json.dumps({
            "from": "anyclaw", "to": "factory", "type": "task_request",
            "message": "request A", "msg_id": "req-a",
            "context": {"request_type": "work_request", "params": {}},
        }) + "\n")
    with open(tmp_b / "ai" / "coordination" / "messages.jsonl", "a") as f:
        f.write(json.dumps({
            "from": "anyclaw", "to": "factory", "type": "task_request",
            "message": "request B", "msg_id": "req-b",
            "context": {"request_type": "work_request", "params": {}},
        }) + "\n")

    intake_a = fri.RequestIntake(repo_root=tmp_a)
    decisions_a = intake_a.admit_once()
    assert len(decisions_a) == 1 and decisions_a[0]["msg_id"] == "req-a"

    intake_b = fri.RequestIntake(repo_root=tmp_b)
    decisions_b = intake_b.admit_once()
    assert len(decisions_b) == 1 and decisions_b[0]["msg_id"] == "req-b"

    # Cross-contamination would leak req-a into B's admission set or state file.
    assert "req-a" not in intake_b.admitted_ids
    assert "req-b" not in intake_a.admitted_ids
    state_a = json.loads((tmp_a / "state" / "request_intake_state.json").read_text())
    state_b = json.loads((tmp_b / "state" / "request_intake_state.json").read_text())
    admitted_a = [d["msg_id"] for d in state_a.get("admissions", [])]
    admitted_b = [d["msg_id"] for d in state_b.get("admissions", [])]
    assert admitted_a == ["req-a"]
    assert admitted_b == ["req-b"]

    for tmp in (tmp_a, tmp_b):
        shutil.rmtree(tmp)


def _write_task_request(msg_id, sender="anyclaw", request_type="work_request", message="Ready for work"):
    """Write a task_request message to the bus."""
    with open(fri.MESSAGES_FILE, "a") as f:
        f.write(json.dumps({
            "from": sender,
            "to": "factory",
            "type": "task_request",
            "message": message,
            "msg_id": msg_id,
            "timestamp": "2026-09-14T17:00:00Z",
            "priority": 7,
            "context": {
                "request_type": request_type,
                "params": {},
            },
        }) + "\n")


def test_happy_path_admitted():
    """Valid task_request from anyclaw is admitted."""
    intake = _make_intake()
    try:
        _write_task_request("req-happy-1")
        decisions = intake.admit_once()
        assert len(decisions) == 1
        assert decisions[0]["admitted"] is True
        assert decisions[0]["from"] == "anyclaw"
        assert decisions[0]["request_type"] == "work_request"
    finally:
        _teardown(intake)


def test_unknown_sender_rejected():
    """Task_request from unregistered sender is rejected."""
    intake = _make_intake()
    try:
        _write_task_request("req-unknown", sender="unknown_agent")
        decisions = intake.admit_once()
        assert len(decisions) == 1
        assert decisions[0]["admitted"] is False
        assert "unknown_sender" in decisions[0]["reason"]
    finally:
        _teardown(intake)


def test_unauthorized_sender_rejected():
    """Task_request from registered but unauthorized sender (operator) is rejected."""
    intake = _make_intake()
    try:
        _write_task_request("req-unauth", sender="operator")
        decisions = intake.admit_once()
        assert len(decisions) == 1
        assert decisions[0]["admitted"] is False
        assert "not_authorized" in decisions[0]["reason"]
    finally:
        _teardown(intake)


def test_low_trust_sender_rejected():
    """Task_request from a registered but unauthorized sender with low trust is rejected."""
    intake = _make_intake()
    try:
        # Add a low-trust registered sender to the party registry
        intake.parties["low_agent"] = {
            "id": "low_agent", "name": "Low Agent", "role": "agent",
            "trust_level": 4, "channels": ["file"],
        }
        # Temporarily authorize this sender so the trust check is exercised
        fri.ALLOWED_SENDERS = frozenset({"anyclaw", "openclaw", "low_agent"})
        # Override party registry file so _validate_sender reads it
        (intake._tmp / "state" / "party_registry.json").write_text(json.dumps(intake.parties))
        _write_task_request("req-lowtrust", sender="low_agent")
        decisions = intake.admit_once()
        assert len(decisions) == 1
        assert decisions[0]["admitted"] is False
        assert "insufficient_trust" in decisions[0]["reason"]
    finally:
        _teardown(intake)


def test_invalid_request_type_rejected():
    """Task_request with unknown request_type is rejected."""
    intake = _make_intake()
    try:
        with open(fri.MESSAGES_FILE, "a") as f:
            f.write(json.dumps({
                "from": "anyclaw", "to": "factory", "type": "task_request",
                "message": "test", "msg_id": "req-badtype-1", "timestamp": "2026-09-14T17:00:00Z",
                "context": {"request_type": "execute_arbitrary_code"},
            }) + "\n")
        decisions = intake.admit_once()
        assert len(decisions) == 1
        assert decisions[0]["admitted"] is False
        assert "invalid_request_type" in decisions[0]["reason"]
    finally:
        _teardown(intake)


def test_missing_request_type_rejected():
    """Task_request with no request_type in context is rejected."""
    intake = _make_intake()
    try:
        with open(fri.MESSAGES_FILE, "a") as f:
            f.write(json.dumps({
                "from": "anyclaw", "to": "factory", "type": "task_request",
                "message": "test", "msg_id": "req-notype-1", "timestamp": "2026-09-14T17:00:00Z",
                "context": {},
            }) + "\n")
        decisions = intake.admit_once()
        assert len(decisions) == 1
        assert decisions[0]["admitted"] is False
        assert "missing_request_type" in decisions[0]["reason"]
    finally:
        _teardown(intake)


def test_dedup_same_msg_id():
    """Same msg_id is never admitted twice."""
    intake = _make_intake()
    try:
        _write_task_request("req-dedup-1")
        d1 = intake.admit_once()
        assert len(d1) == 1

        # Write same msg_id again
        _write_task_request("req-dedup-1")
        d2 = intake.admit_once()
        assert len(d2) == 0  # deduped
    finally:
        _teardown(intake)


def test_restart_does_not_re_admit():
    """After restart (new RequestIntake from same state), already-admitted IDs persist."""
    intake = _make_intake()
    try:
        _write_task_request("req-restart-1")
        _write_task_request("req-restart-2")
        d1 = intake.admit_once()
        assert len(d1) == 2

        # Simulate restart: create a fresh checkout-local intake from the same repo root
        intake2 = fri.RequestIntake(repo_root=intake._tmp)

        d2 = intake2.admit_once()
        assert len(d2) == 0  # already in state, no re-admit
    finally:
        _teardown(intake)


def test_oversized_message_rejected():
    """Message exceeding MAX_MESSAGE_LENGTH is rejected."""
    intake = _make_intake()
    try:
        long_msg = "x" * 3000
        with open(fri.MESSAGES_FILE, "a") as f:
            f.write(json.dumps({
                "from": "anyclaw", "to": "factory", "type": "task_request",
                "message": long_msg, "msg_id": "req-long-1", "timestamp": "2026-09-14T17:00:00Z",
                "context": {"request_type": "question"},
            }) + "\n")
        decisions = intake.admit_once()
        assert len(decisions) == 1
        assert decisions[0]["admitted"] is False
        assert "too_long" in decisions[0]["reason"]
    finally:
        _teardown(intake)


def test_empty_message_rejected():
    """Empty message body is rejected."""
    intake = _make_intake()
    try:
        with open(fri.MESSAGES_FILE, "a") as f:
            f.write(json.dumps({
                "from": "anyclaw", "to": "factory", "type": "task_request",
                "message": "", "msg_id": "req-empty-1", "timestamp": "2026-09-14T17:00:00Z",
                "context": {"request_type": "status_probe"},
            }) + "\n")
        decisions = intake.admit_once()
        assert len(decisions) == 1
        assert decisions[0]["admitted"] is False
        assert "empty_message" in decisions[0]["reason"]
    finally:
        _teardown(intake)


def test_missing_msg_id_rejected():
    """Message with no msg_id is rejected."""
    intake = _make_intake()
    try:
        with open(fri.MESSAGES_FILE, "a") as f:
            f.write(json.dumps({
                "from": "anyclaw", "to": "factory", "type": "task_request",
                "message": "test", "timestamp": "2026-09-14T17:00:00Z",
                "context": {"request_type": "work_request"},
            }) + "\n")
        decisions = intake.admit_once()
        assert len(decisions) == 1
        assert decisions[0]["admitted"] is False
        assert "missing_msg_id" in decisions[0]["reason"]
    finally:
        _teardown(intake)


def test_no_auto_dispatch():
    """Admitted requests do NOT produce task_assignments on the bus."""
    intake = _make_intake()
    try:
        _write_task_request("req-nodispatch-1")
        intake.admit_once()

        # Read bus: should still have exactly 1 message (the original request)
        with open(fri.MESSAGES_FILE) as f:
            lines = [l for l in f if l.strip()]
        assignments = [
            json.loads(l) for l in lines
            if json.loads(l).get("type") == "task_assignment"
        ]
        assert len(assignments) == 0, f"Expected 0 auto-dispatched assignments, got {len(assignments)}"
    finally:
        _teardown(intake)


def test_all_allowed_request_types():
    """All three allowed request types are accepted (from authorized sender)."""
    for rtype in fri.ALLOWED_REQUEST_TYPES:
        intake = _make_intake()
        try:
            _write_task_request(f"req-{rtype}-1", request_type=rtype, message=f"Test {rtype}")
            decisions = intake.admit_once()
            assert len(decisions) == 1, f"Expected 1 decision for {rtype}"
            assert decisions[0]["admitted"] is True, f"{rtype} should be admitted"
        finally:
            _teardown(intake)


def test_status_summary():
    """Status returns correct counts."""
    intake = _make_intake()
    try:
        _write_task_request("req-status-1")
        _write_task_request("req-status-2")
        intake.admit_once()
        s = intake.status()
        assert s["admitted_count"] == 2
        assert s["rejected_count"] == 0
        assert s["pending_requests"] == 0
    finally:
        _teardown(intake)


def test_non_task_request_messages_ignored():
    """Non-task_request messages on the bus are not processed."""
    intake = _make_intake()
    try:
        with open(fri.MESSAGES_FILE, "a") as f:
            f.write(json.dumps({
                "from": "factory", "to": "anyclaw", "type": "task_assignment",
                "message": "do something", "msg_id": "task-001",
                "timestamp": "2026-09-14T17:00:00Z",
            }) + "\n")
            f.write(json.dumps({
                "from": "anyclaw", "to": "factory", "type": "continuation_event",
                "message": "done", "msg_id": "evt-001",
                "timestamp": "2026-09-14T17:00:01Z",
            }) + "\n")
        decisions = intake.admit_once()
        assert len(decisions) == 0
    finally:
        _teardown(intake)
