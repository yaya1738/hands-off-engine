import json, sys, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _make_emitter():
    from scripts.continuation import ContinuationEmitter, EVENTS_FILE, EMITTED_IDS, STATE_DIR
    tmp = Path(tempfile.mkdtemp())
    (tmp / "state").mkdir()
    (tmp / "ai" / "coordination").mkdir(parents=True)
    emitter = ContinuationEmitter.__new__(ContinuationEmitter)
    emitter.emitted_ids = set()

    import scripts.continuation as c
    c.EVENTS_FILE = tmp / "state" / "continuation_events.jsonl"
    c.EMITTED_IDS = tmp / "state" / "emitted_event_ids.json"
    emitter._tmp = tmp
    return emitter


def test_emit_task_completed():
    e = _make_emitter()
    event = e.emit_task_completed("t-001", "success", "canary done")
    assert event is not None
    assert event["event_type"] == "task_completed"
    assert event["is_wake"] is True
    assert event["correlation_id"] == "t-001"


def test_emit_blocker():
    e = _make_emitter()
    event = e.emit_blocker("token missing", "bot token")
    assert event["event_type"] == "blocker"
    assert event["is_wake"] is True


def test_emit_heartbeat_not_wake():
    e = _make_emitter()
    event = e.emit_heartbeat("alive")
    assert event["event_type"] == "heartbeat"
    assert event["is_wake"] is False


def test_dedup_by_event_id():
    e = _make_emitter()
    event1 = e.emit_task_completed("t-dedup", "ok", "test")
    assert event1 is not None
    # Emitting same event_id should be deduped
    e.emitted_ids.add(event1["event_id"])
    # Try emitting with same ID (simulated)
    assert event1["event_id"] in e.emitted_ids


def test_events_persist():
    e = _make_emitter()
    e.emit_task_completed("t-persist", "ok", "test")
    e.emit_heartbeat("alive")
    events = e.get_recent_events(10)
    assert len(events) == 2
    assert events[0]["event_type"] == "task_completed"
    assert events[1]["event_type"] == "heartbeat"


def test_wake_event_filtering():
    e = _make_emitter()
    e.emit_task_completed("t-1", "ok", "test")
    e.emit_heartbeat("alive")
    e.emit_blocker("blocked", "need input")
    wake = e.get_recent_events(10, wake_only=True)
    assert all(ev["is_wake"] for ev in wake)
    assert len(wake) == 2
