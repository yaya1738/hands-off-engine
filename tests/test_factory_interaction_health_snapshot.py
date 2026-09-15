from scripts.factory_interaction_health import project_factory_interaction_metrics


def test_projects_admission_from_shared_snapshot_without_secret_or_text():
    snapshot = {
        "correlation_health": {
            "available": True,
            "event_count": 4,
            "correlated_event_count": 3,
            "orphan_reply_count": 1,
            "single_event_count": 0,
            "explicit_task_thread_coverage": 0.5,
            "window": {"truncated": True},
            "secret": "must-not-escape",
        },
        "admission_observation": {
            "available": True,
            "msg_id": "msg-1",
            "reply_to": "msg-1",
            "task_id": "task-1",
            "admitted": True,
            "reason": "accepted",
            "decided_at": "2026-09-15T07:00:00Z",
            "message": "must-not-escape",
            "secret": "must-not-escape",
        },
    }

    assert project_factory_interaction_metrics(snapshot) == {
        "available": True,
        "interaction_health": snapshot["correlation_health"],
        "interaction_event_count": 4,
        "interaction_correlated_event_count": 3,
        "interaction_correlation_rate": 0.75,
        "interaction_orphan_reply_count": 1,
        "interaction_single_event_count": 0,
        "interaction_task_thread_coverage": 0.5,
        "interaction_window_truncated": True,
        "admission_observation": {
            "available": True,
            "msg_id": "msg-1",
            "reply_to": "msg-1",
            "task_id": "task-1",
            "admitted": True,
            "reason": "accepted",
            "decided_at": "2026-09-15T07:00:00Z",
        },
    }


def test_missing_shared_observation_fails_closed():
    assert project_factory_interaction_metrics({}) == {"available": False}
