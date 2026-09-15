from scripts.control_room_state import build_snapshot


def test_control_room_projects_admission_from_canonical_bus(tmp_path):
    bus = tmp_path / "ai" / "coordination"
    bus.mkdir(parents=True)
    (bus / "messages.jsonl").write_text(
        '{"type":"inbound_from_agent","msg_id":"outer-1",'
        '"payload":{"event_type":"task_admission","decision":{'
        '"msg_id":"req-1","reply_to":"req-1","task_id":"task-1",'
        '"admitted":true,"reason":"ok","secret":"hidden"}}}\n'
    )

    snapshot = build_snapshot(tmp_path, bus_limit=20)

    assert snapshot["admission_observation"] == {
        "available": True,
        "msg_id": "req-1",
        "reply_to": "req-1",
        "task_id": "task-1",
        "admitted": True,
        "reason": "ok",
        "decided_at": None,
    }
    assert "secret" not in snapshot["admission_observation"]


def test_control_room_fails_closed_without_canonical_admission_event(tmp_path):
    bus = tmp_path / "ai" / "coordination"
    bus.mkdir(parents=True)
    (bus / "messages.jsonl").write_text('{"type":"task_request","msg_id":"req-1"}\n')

    snapshot = build_snapshot(tmp_path, bus_limit=20)

    assert snapshot["admission_observation"] == {"available": False}
