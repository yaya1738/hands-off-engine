from scripts.factory_outcome_observability import project_factory_outcomes


def test_projects_explicit_task_result_identity_and_status():
    result = project_factory_outcomes([
        {"type": "task_result", "msg_id": "m-1", "reply_to": "m-0", "timestamp": "now", "context": {"task_id": "t-1", "status": "success", "secret": "x"}},
    ])
    assert result["available"] is True
    assert result["outcome_count"] == 1
    assert result["outcomes"] == [{"msg_id": "m-1", "task_id": "t-1", "reply_to": "m-0", "status": "success", "timestamp": "now"}]


def test_unrelated_events_are_ignored():
    result = project_factory_outcomes([{"type": "coordination", "message": "ignored"}])
    assert result == {"available": False, "outcome_count": 0, "outcomes": []}


def test_missing_identity_fails_closed_per_event():
    result = project_factory_outcomes([{"type": "task_result", "context": {"status": "success"}}])
    assert result == {"available": False, "outcome_count": 0, "outcomes": []}


def test_outcomes_are_bounded():
    events = [
        {"type": "task_result", "msg_id": f"m-{i}", "context": {"task_id": f"t-{i}", "status": "success"}}
        for i in range(4)
    ]
    result = project_factory_outcomes(events, limit=2)
    assert [item["msg_id"] for item in result["outcomes"]] == ["m-2", "m-3"]
