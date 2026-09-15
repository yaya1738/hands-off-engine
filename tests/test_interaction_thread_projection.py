from scripts.interaction_thread_projection import project_threads


def test_correlates_explicit_task_chain_and_enriches_lifecycle():
    events = [
        {"type": "task_assignment", "msg_id": "m1", "context": {"task_id": "t1"}},
        {"type": "task_result", "msg_id": "m2", "context": {"task_id": "t1", "reply_to": "m1"}},
        {"type": "continuation_event", "msg_id": "m3", "context": {"task_id": "t1", "reply_to": "m2"}},
    ]
    threads = project_threads(events, {"t1": {"current_state": "completed"}})
    assert len(threads) == 1
    assert threads[0]["correlation_key"] == "task:t1"
    assert threads[0]["task_id"] == "t1"
    assert threads[0]["lifecycle_state"] == "completed"
    assert len(threads[0]["events"]) == 3
    assert threads[0]["correlation_quality"] == "correlated"


def test_missing_task_id_remains_single_event_without_inference():
    events = [{"type": "a", "msg_id": "m1"}, {"type": "b", "msg_id": "m2"}]
    threads = project_threads(events, {})
    assert [thread["correlation_key"] for thread in threads] == ["msg:m1", "msg:m2"]
    assert all(thread["correlation_quality"] == "single_event" for thread in threads)


def test_orphan_reply_is_visible_and_not_grouped_by_proximity():
    events = [{"type": "task_result", "msg_id": "m2", "reply_to": "missing"}, {"type": "unrelated", "msg_id": "m3"}]
    threads = project_threads(events, {})
    assert threads[0]["correlation_quality"] == "orphan_reply"
    assert threads[0]["correlation_kind"] == "reply"
    assert threads[1]["correlation_key"] == "msg:m3"


def test_projection_is_bounded():
    events = [{"type": "x", "msg_id": f"m{i}"} for i in range(10)]
    threads = project_threads(events, {}, limit=3, events_per_thread=1)
    assert len(threads) == 3
    assert all(len(thread["events"]) <= 1 for thread in threads)


def test_reply_only_event_can_correlate_to_explicit_message():
    events = [{"type": "request", "msg_id": "m1"}, {"type": "reply", "msg_id": "m2", "reply_to": "m1"}]
    threads = project_threads(events, {})
    assert threads[1]["correlation_key"] == "reply:m1"
    assert threads[1]["correlation_quality"] == "correlated"


def test_reply_before_target_inherits_explicit_task_order_independently():
    events = [
        {"type": "reply", "msg_id": "m2", "context": {"reply_to": "m1"}},
        {"type": "request", "msg_id": "m1", "context": {"task_id": "t1"}},
    ]
    threads = project_threads(events, {})
    assert len(threads) == 1
    assert threads[0]["correlation_key"] == "task:t1"
    assert threads[0]["correlation_quality"] == "correlated"


def test_task_id_wins_over_reply_target():
    events = [
        {"type": "request", "msg_id": "m1", "context": {"task_id": "t1"}},
        {"type": "result", "msg_id": "m2", "context": {"task_id": "t2", "reply_to": "m1"}},
    ]
    threads = project_threads(events, {})
    assert [thread["correlation_key"] for thread in threads] == ["task:t1", "task:t2"]
