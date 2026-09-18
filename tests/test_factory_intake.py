import json, sys, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.factory_intake as fi


def _make_intake():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "state").mkdir()
    (tmp / "ai" / "coordination").mkdir(parents=True)
    (tmp / "state" / "intake_decisions").mkdir()

    intake = fi.FactoryIntake.__new__(fi.FactoryIntake)
    intake.repo_root = tmp
    intake.state_dir = tmp / "state"
    intake.decisions_dir = tmp / "state" / "intake_decisions"
    intake.consumed_ids = set()
    intake.decisions = []
    intake.state = {"consumed_ids": [], "decisions": []}

    fi.MESSAGES_FILE = tmp / "ai" / "coordination" / "messages.jsonl"
    fi.INTAKE_STATE = tmp / "state" / "factory_intake_state.json"
    fi.DECISION_DIR = tmp / "state" / "intake_decisions"

    intake._tmp = tmp
    return intake


def _write_msg(msg):
    with open(fi.MESSAGES_FILE, "a") as f:
        f.write(json.dumps(msg) + "\n")


def test_dedup_same_event_twice():
    """Duplicate events are consumed exactly once."""
    intake = _make_intake()
    msg = {
        "type": "continuation_event",
        "event_id": "evt-001",
        "context": {"event_type": "task_completed", "is_wake": True, "task_id": "t-dedup"},
        "message": "done",
    }
    _write_msg(msg)
    _write_msg(msg)

    decisions = intake.intake_once()
    assert len(decisions) == 1, f"Should consume once, got {len(decisions)}"


def test_restart_does_not_fan_out():
    """After restart (new FactoryIntake from same state), no duplicate decisions."""
    tmp_path = None
    # First run
    intake = _make_intake()
    tmp_path = intake._tmp
    msg = {
        "type": "continuation_event",
        "event_id": "evt-restart",
        "context": {"event_type": "task_completed", "is_wake": True, "task_id": "t-restart"},
        "message": "restart test",
    }
    _write_msg(msg)
    decisions1 = intake.intake_once()
    assert len(decisions1) == 1

    # Simulate restart: load state from disk
    fi.INTAKE_STATE = tmp_path / "state" / "factory_intake_state.json"
    intake2 = fi.FactoryIntake()
    intake2.repo_root = tmp_path
    intake2.state_dir = tmp_path / "state"
    intake2.decisions_dir = tmp_path / "state" / "intake_decisions"
    intake2.state = fi._load_state()
    intake2.consumed_ids = set(intake2.state.get("consumed_ids", []))
    intake2.decisions = list(intake2.state.get("decisions", []))

    decisions2 = intake2.intake_once()
    assert len(decisions2) == 0, f"Restart should not fan out: got {len(decisions2)}"


def test_non_wake_filtered():
    """Heartbeat/non-wake events produce no decision."""
    intake = _make_intake()
    msg = {
        "type": "continuation_event",
        "event_id": "evt-hb",
        "context": {"event_type": "heartbeat", "is_wake": False},
        "message": "alive",
    }
    _write_msg(msg)
    decisions = intake.intake_once()
    assert len(decisions) == 0


def test_correlation_preserves_task_id():
    """Decision preserves the original task_id correlation."""
    intake = _make_intake()
    msg = {
        "type": "continuation_event",
        "event_id": "evt-corr",
        "context": {"event_type": "blocked", "is_wake": True, "task_id": "t-corr-42"},
        "message": "blocked",
    }
    _write_msg(msg)
    decisions = intake.intake_once()
    assert len(decisions) == 1
    assert decisions[0]["task_id"] == "t-corr-42"


def test_emits_exactly_one_assignment():
    """Each processed event emits exactly one task_assignment to anyclaw."""
    intake = _make_intake()
    for i in range(3):
        _write_msg({
            "type": "continuation_event",
            "event_id": f"evt-multi-{i}",
            "context": {"event_type": "security_boundary", "is_wake": True, "task_id": f"t-multi-{i}"},
            "message": f"security {i}",
        })
    decisions = intake.intake_once()
    assert len(decisions) == 3

    # Verify exactly 3 task_assignments written to messages.jsonl
    assignments = []
    with open(fi.MESSAGES_FILE) as f:
        for line in f:
            if line.strip():
                msg = json.loads(line)
                if msg.get("type") == "task_assignment":
                    assignments.append(msg)
    assert len(assignments) == 3, f"Expected 3 assignments, got {len(assignments)}"
    for a in assignments:
        assert a["from"] == "factory"
        assert a["to"] == "anyclaw"
        assert "task_assignment" in a["type"]


def test_all_wake_types_accepted():
    """All Factory round 12 wake-worthy types accepted."""
    for wake_type in fi.WAKE_EVENT_TYPES:
        intake = _make_intake()
        _write_msg({
            "type": "continuation_event",
            "event_id": f"evt-{wake_type}",
            "context": {"event_type": wake_type, "is_wake": True},
            "message": f"test {wake_type}",
        })
        decisions = intake.intake_once()
        assert len(decisions) == 1, f"Wake type {wake_type} should be accepted"




def test_task_completed_without_explicit_action_not_promoted():
    """task_completed without an explicit next action is not promoted (fail-closed)."""
    intake = _make_intake()
    _write_msg({
        "type": "continuation_event",
        "event_id": "evt-generic-done",
        "context": {"event_type": "task_completed", "is_wake": True, "task_id": "t-generic", "status": "success"},
        "message": "done",
    })
    decisions = intake.intake_once()
    assert len(decisions) == 1
    assert decisions[0]["assigned_msg_id"] is None
    assert decisions[0]["reason"] == "no_explicit_next_action"

    assignments = []
    with open(fi.MESSAGES_FILE) as f:
        for line in f:
            if line.strip() and json.loads(line).get("type") == "task_assignment":
                assignments.append(json.loads(line))
    assert assignments == [], "Generic task_completed must not fan out an assignment"


def test_task_completed_with_explicit_action_promoted():
    """task_completed with an explicit next_action is promoted with that exact spec."""
    intake = _make_intake()
    _write_msg({
        "type": "continuation_event",
        "event_id": "evt-explicit-done",
        "context": {
            "event_type": "task_completed",
            "is_wake": True,
            "task_id": "t-explicit",
            "status": "success",
            "next_action": {"action": "verify_checkout", "params": {"path": "scripts/factory_intake.py"}, "reply_to": "t-explicit"},
        },
        "message": "done",
    })
    decisions = intake.intake_once()
    assert len(decisions) == 1
    assert decisions[0]["assigned_msg_id"] is not None

    assignments = []
    with open(fi.MESSAGES_FILE) as f:
        for line in f:
            if line.strip() and json.loads(line).get("type") == "task_assignment":
                assignments.append(json.loads(line))
    assert len(assignments) == 1
    ctx = assignments[0]["context"]
    assert ctx["action"] == "verify_checkout"
    assert ctx["params"] == {"path": "scripts/factory_intake.py"}
    assert ctx["reply_to"] == "t-explicit"
    assert ctx["source_task_id"] == "t-explicit"
    assert ctx["source_event"] == "evt-explicit-done"
    assert ctx["reply_to"] != "281"




def test_task_completed_without_next_action_does_not_fan_out():
    """Generic completion is observed but must not create a new assignment."""
    intake = _make_intake()
    _write_msg({
        "type": "continuation_event",
        "event_id": "evt-no-next",
        "context": {"event_type": "task_completed", "is_wake": True, "task_id": "t-no-next", "status": "success"},
        "message": "completed successfully",
    })
    decisions = intake.intake_once()
    assert len(decisions) == 1
    assert decisions[0]["assigned_msg_id"] is None

    with open(fi.MESSAGES_FILE) as f:
        assignments = [json.loads(line) for line in f if line.strip() and json.loads(line).get("type") == "task_assignment"]
    assert assignments == []


def test_task_completed_with_string_next_action_fans_out():
    """A non-empty string next_action authorizes intentional continuation fan-out."""
    intake = _make_intake()
    _write_msg({
        "type": "continuation_event",
        "event_id": "evt-next",
        "context": {"event_type": "task_completed", "is_wake": True, "task_id": "t-next", "status": "success", "next_action": "run system_status"},
        "message": "completed; continue with status check",
    })
    decisions = intake.intake_once()
    assert len(decisions) == 1
    assert decisions[0]["assigned_msg_id"] is not None

    with open(fi.MESSAGES_FILE) as f:
        assignments = [json.loads(line) for line in f if line.strip() and json.loads(line).get("type") == "task_assignment"]
    assert len(assignments) == 1
    assert assignments[0]["context"]["source_event"] == "evt-next"


def test_pending_wake_events():
    """pending_wake_events returns unconsumed wake events."""
    intake = _make_intake()
    _write_msg({"type": "continuation_event", "event_id": "evt-p1", "context": {"event_type": "task_completed", "is_wake": True}, "message": "done"})
    _write_msg({"type": "continuation_event", "event_id": "evt-p2", "context": {"event_type": "heartbeat", "is_wake": False}, "message": "alive"})

    pending = intake.pending_wake_events()
    assert len(pending) == 1


def test_assignment_written_to_bus():
    """Task assignment goes to canonical messages.jsonl."""
    intake = _make_intake()
    msg = {
        "type": "continuation_event",
        "event_id": "evt-bus",
        "context": {"event_type": "test_failure", "is_wake": True, "task_id": "t-bus"},
        "message": "test fail",
    }
    _write_msg(msg)
    intake.intake_once()

    # Read messages.jsonl, find our assignment
    with open(fi.MESSAGES_FILE) as f:
        lines = [json.loads(l) for l in f if l.strip()]
    assignments = [l for l in lines if l.get("type") == "task_assignment"]
    assert len(assignments) == 1
    assert assignments[0]["context"]["task_id"].startswith("intake-")
    assert assignments[0]["context"]["source_event"] == "evt-bus"


def test_blocked_without_explicit_action_does_not_fan_out():
    """A blocked wake is observable but cannot self-authorize a follow-up assignment."""
    intake = _make_intake()
    _write_msg({
        "type": "continuation_event",
        "event_id": "evt-blocked-no-next",
        "context": {"event_type": "blocked", "is_wake": True, "task_id": "t-blocked-no-next"},
        "message": "blocked without declared recovery action",
    })
    decisions = intake.intake_once()
    assert len(decisions) == 1
    assert decisions[0]["assigned_msg_id"] is None
    assert decisions[0]["reason"] == "no_explicit_next_action"


def test_intake_once_respects_max_events():
    """Bounded intake consumes at most the requested number of decisions."""
    intake = _make_intake()
    for i in range(3):
        _write_msg({"type": "continuation_event", "event_id": f"evt-bound-{i}", "context": {"event_type": "task_completed", "is_wake": True, "task_id": f"t-bound-{i}"}, "message": "done"})
    decisions = intake.intake_once(max_events=1)
    assert len(decisions) == 1
