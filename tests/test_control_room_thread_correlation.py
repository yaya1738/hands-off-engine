"""Explicit interaction thread correlation invariants (PR #304 hardening)."""
from scripts.interaction_thread_projection import project_threads


def test_task_id_has_precedence_over_reply_to():
    events = [
        {"type": "request", "msg_id": "m1", "context": {"task_id": "t1"}},
        {"type": "result", "msg_id": "m2", "context": {"task_id": "t2", "reply_to": "m1"}},
    ]
    threads = project_threads(events, {})
    assert [t["correlation_key"] for t in threads] == ["task:t1", "task:t2"]


def test_reply_links_to_observed_message_and_inherits_target_task():
    events = [
        {"type": "request", "msg_id": "m1", "context": {"task_id": "t1"}},
        {"type": "reply", "msg_id": "m2", "context": {"reply_to": "m1"}},
    ]
    threads = project_threads(events, {})
    assert len(threads) == 1
    assert threads[0]["correlation_key"] == "task:t1"
    assert [e["msg_id"] for e in threads[0]["events"]] == ["m1", "m2"]
    assert threads[0]["events"][1]["correlation_quality"] == "correlated"


def test_reply_correlation_is_order_independent():
    events = [
        {"type": "reply", "msg_id": "m2", "reply_to": "m1"},
        {"type": "request", "msg_id": "m1", "context": {"task_id": "t1"}},
    ]
    threads = project_threads(events, {})
    assert len(threads) == 1
    assert threads[0]["correlation_key"] == "task:t1"


def test_missing_reply_target_remains_orphan():
    events = [
        {"type": "reply", "msg_id": "m2", "reply_to": "missing"},
        {"type": "unrelated", "msg_id": "m3"},
    ]
    threads = project_threads(events, {})
    assert threads[0]["correlation_key"] == "orphan:m2"
    assert threads[0]["correlation_quality"] == "orphan_reply"
    assert threads[1]["correlation_key"] == "msg:m3"


def test_adjacent_messages_without_explicit_links_stay_separate():
    events = [
        {"type": "a", "msg_id": "m1"},
        {"type": "b", "msg_id": "m2"},
    ]
    threads = project_threads(events, {})
    assert [t["correlation_key"] for t in threads] == ["msg:m1", "msg:m2"]


def test_thread_limit_is_bounded():
    events = [{"type": "x", "msg_id": f"m{i}"} for i in range(20)]
    threads = project_threads(events, {}, limit=3)
    assert len(threads) == 3
