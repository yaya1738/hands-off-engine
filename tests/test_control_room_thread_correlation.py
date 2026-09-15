from scripts.control_room_state import _build_threads


def test_task_id_has_precedence_over_reply_to():
    events = [
        {"type": "request", "msg_id": "m1", "context": {"task_id": "t1"}},
        {"type": "result", "msg_id": "m2", "context": {"task_id": "t2", "reply_to": "m1"}},
    ]
    result = _build_threads(events, {})
    assert [thread["key"] for thread in result["threads"]] == ["task:t1", "task:t2"]


def test_reply_links_to_observed_message_and_inherits_target_task():
    events = [
        {"type": "request", "msg_id": "m1", "context": {"task_id": "t1"}},
        {"type": "reply", "msg_id": "m2", "context": {"reply_to": "m1"}},
    ]
    result = _build_threads(events, {})
    assert len(result["threads"]) == 1
    assert result["threads"][0]["key"] == "task:t1"
    assert [event["msg_id"] for event in result["threads"][0]["events"]] == ["m1", "m2"]
    assert result["threads"][0]["events"][1]["correlation_quality"] == "correlated"


def test_reply_correlation_is_order_independent():
    events = [
        {"type": "reply", "msg_id": "m2", "reply_to": "m1"},
        {"type": "request", "msg_id": "m1", "context": {"task_id": "t1"}},
    ]
    result = _build_threads(events, {})
    assert len(result["threads"]) == 1
    assert result["threads"][0]["key"] == "task:t1"


def test_missing_reply_target_remains_orphan():
    events = [
        {"type": "reply", "msg_id": "m2", "reply_to": "missing"},
        {"type": "unrelated", "msg_id": "m3"},
    ]
    result = _build_threads(events, {})
    assert result["threads"][0]["key"] == "orphan:m2"
    assert result["threads"][0]["correlation_quality"] == "orphan_reply"
    assert result["threads"][1]["key"] == "msg:m3"


def test_adjacent_messages_without_explicit_links_stay_separate():
    events = [
        {"type": "a", "msg_id": "m1"},
        {"type": "b", "msg_id": "m2"},
    ]
    result = _build_threads(events, {})
    assert [thread["key"] for thread in result["threads"]] == ["msg:m1", "msg:m2"]


def test_thread_limit_is_bounded():
    events = [{"type": "x", "msg_id": f"m{i}"} for i in range(20)]
    result = _build_threads(events, {}, limit=3)
    assert result["count"] == 3
    assert len(result["threads"]) == 3
