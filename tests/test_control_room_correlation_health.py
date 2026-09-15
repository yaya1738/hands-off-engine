from scripts.control_room_state import build_snapshot


def test_snapshot_exposes_bounded_correlation_health(tmp_path):
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    bus.parent.mkdir(parents=True)
    bus.write_text(
        '{"type":"request","msg_id":"m1","context":{"task_id":"t1"}}\n'
        '{"type":"reply","msg_id":"m2","context":{"reply_to":"m1"}}\n'
        '{"type":"reply","msg_id":"m3","context":{"reply_to":"missing"}}\n'
        '{"type":"other","msg_id":"m4"}\n'
    )
    health = build_snapshot(tmp_path, bus_limit=4, lifecycle_limit=0)["correlation_health"]
    assert health["event_count"] == 4
    assert health["correlated_event_count"] == 2
    assert health["orphan_reply_count"] == 1
    assert health["single_event_count"] == 1
    assert health["explicit_task_event_count"] == 1
    assert health["explicit_task_thread_coverage"] == 0.25
    assert health["bounded_window_truncated"] is True


def test_correlation_health_is_empty_without_events(tmp_path):
    health = build_snapshot(tmp_path, bus_limit=10, lifecycle_limit=0)["correlation_health"]
    assert health["available"] is False
    assert health["event_count"] == 0
    assert health["explicit_task_thread_coverage"] is None
    assert health["bounded_window_truncated"] is False
