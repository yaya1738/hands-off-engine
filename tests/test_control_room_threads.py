"""Bounded interaction thread view — explicit-correlation-only, read-only."""
import json

from scripts.control_room_state import build_snapshot


def _seed_bus(tmp_path, events):
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    bus.parent.mkdir(parents=True)
    bus.write_text("\n".join(json.dumps(e) for e in events) + "\n")


def _seed_lifecycle(tmp_path, tasks):
    state = tmp_path / "state"
    state.mkdir(parents=True, exist_ok=True)
    (state / "task_lifecycle.json").write_text(json.dumps(tasks))


def test_thread_joins_result_to_assignment_via_task_id(tmp_path):
    _seed_bus(tmp_path, [
        {"type": "task_assignment", "msg_id": "assign-1", "timestamp": "2026-09-15T00:00:00+00:00", "context": {"task_id": "t-1"}},
        {"type": "task_result", "msg_id": "t-1", "timestamp": "2026-09-15T00:01:00+00:00", "context": {"task_id": "t-1", "status": "success"}},
    ])
    _seed_lifecycle(tmp_path, {"t-1": {"states": {"sent": "2026-09-15T00:00:00+00:00", "completed": "2026-09-15T00:01:00+00:00", "result_published": "2026-09-15T00:01:05+00:00"}}})
    snapshot = build_snapshot(tmp_path, bus_limit=50, lifecycle_limit=50)
    threads = snapshot["threads"]["threads"]
    assert snapshot["threads"]["available"] is True
    assert len(threads) == 1
    thread = threads[0]
    assert thread["key"] == "t-1"
    assert len(thread["events"]) == 2
    assert [e["type"] for e in thread["events"]] == ["task_assignment", "task_result"]
    assert thread["events"][1]["lifecycle_state"] == "result_published"


def test_thread_joins_via_explicit_reply_to_only(tmp_path):
    _seed_bus(tmp_path, [
        {"type": "task_request", "msg_id": "req-1", "timestamp": "2026-09-15T00:00:00+00:00", "context": {}},
        {"type": "task_assignment", "msg_id": "assign-2", "timestamp": "2026-09-15T00:01:00+00:00", "context": {"task_id": "t-2", "reply_to": "req-1"}},
    ])
    snapshot = build_snapshot(tmp_path, bus_limit=50, lifecycle_limit=50)
    threads = snapshot["threads"]["threads"]
    assert len(threads) == 1
    assert threads[0]["key"] == "req-1"
    assert len(threads[0]["events"]) == 2


def test_unrelated_events_stay_separate_no_proximity_inference(tmp_path):
    _seed_bus(tmp_path, [
        {"type": "task_assignment", "msg_id": "a-1", "timestamp": "2026-09-15T00:00:00+00:00", "context": {"task_id": "t-1"}},
        {"type": "task_assignment", "msg_id": "a-2", "timestamp": "2026-09-15T00:00:01+00:00", "context": {"task_id": "t-2"}},
    ])
    snapshot = build_snapshot(tmp_path, bus_limit=50, lifecycle_limit=50)
    threads = snapshot["threads"]["threads"]
    assert len(threads) == 2
    assert {t["key"] for t in threads} == {"t-1", "t-2"}
    assert all(len(t["events"]) == 1 for t in threads)


def test_thread_view_is_bounded(tmp_path):
    events = []
    for i in range(15):
        events.append({"type": "task_assignment", "msg_id": f"a-{i}", "timestamp": f"2026-09-15T00:{i:02d}:00+00:00", "context": {"task_id": f"t-{i}"}})
    _seed_bus(tmp_path, events)
    snapshot = build_snapshot(tmp_path, bus_limit=50, lifecycle_limit=50, thread_limit=5)
    assert snapshot["threads"]["count"] == 5
    assert len(snapshot["threads"]["threads"]) == 5


def test_missing_ids_render_unknown(tmp_path):
    _seed_bus(tmp_path, [
        {"type": "continuation_event", "timestamp": "2026-09-15T00:00:00+00:00", "context": {}},
    ])
    snapshot = build_snapshot(tmp_path, bus_limit=50, lifecycle_limit=50)
    threads = snapshot["threads"]["threads"]
    assert len(threads) == 1
    assert threads[0]["key"].startswith("unknown-")
    event = threads[0]["events"][0]
    assert event["msg_id"] == "unknown"
    assert event["task_id"] == "unknown"
    assert event["lifecycle_state"] == "unknown"


def test_empty_bus_thread_view_unavailable(tmp_path):
    snapshot = build_snapshot(tmp_path, bus_limit=50, lifecycle_limit=50)
    assert snapshot["threads"]["available"] is False
    assert snapshot["threads"]["count"] == 0
