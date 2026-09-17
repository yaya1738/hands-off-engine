from scripts.learning_observability import project_learning_observation


def test_projects_explicit_task_results_without_payload_details():
    lifecycle = [
        {"states": {"sent": "t1", "completed": "t2", "observed": "t3"}},
        {"states": {"sent": "t4", "completed": "t5"}},
    ]
    events = [
        {"type": "task_result", "msg_id": "m1", "context": {"task_id": "t1", "status": "success", "secret": "nope"}},
        {"type": "task_result", "msg_id": "m2", "context": {"task_id": "t4", "status": "failed", "result": {"secret": "nope"}}},
        {"type": "heartbeat", "msg_id": "h1", "context": {"status": "success"}},
    ]

    result = project_learning_observation(lifecycle, events)

    assert result == {
        "available": True,
        "lifecycle_entry_count": 2,
        "completed_count": 2,
        "observed_count": 1,
        "outcome_count": 2,
        "success_count": 1,
        "failure_count": 1,
        "outcome_observation_rate": 0.5,
    }


def test_ignores_malformed_and_non_result_events():
    assert project_learning_observation([], [{"type": "heartbeat"}, {"type": "task_result", "context": {}}]) == {"available": False}
