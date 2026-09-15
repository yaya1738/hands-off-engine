from scripts.factory_decision_context import build_factory_decision_context


def test_decision_context_projects_shared_observation_without_secrets():
    snapshot = {
        "correlation_health": {
            "available": True,
            "event_count": 4,
            "correlated_event_count": 2,
            "orphan_reply_count": 1,
            "single_event_count": 1,
            "explicit_task_thread_coverage": 0.5,
            "window": {"truncated": False},
            "secret": "no",
        },
        "admission_observation": {
            "available": True,
            "msg_id": "m-1",
            "reply_to": "m-1",
            "task_id": "t-1",
            "admitted": True,
            "reason": "accepted",
            "decided_at": "2026-09-15T07:00:00Z",
            "message": "must not escape",
        },
        "factory_assessment": {
            "available": True,
            "health": 0.9,
            "gaps": [],
            "objective": "observe",
            "secret": "no",
        },
    }

    assert build_factory_decision_context(snapshot) == {
        "available": True,
        "interaction": {
            "correlation_rate": 0.5,
            "orphan_reply_count": 1,
            "single_event_count": 1,
            "task_thread_coverage": 0.5,
            "window_truncated": False,
        },
        "admission": {
            "available": True,
            "msg_id": "m-1",
            "reply_to": "m-1",
            "task_id": "t-1",
            "admitted": True,
            "reason": "accepted",
            "decided_at": "2026-09-15T07:00:00Z",
        },
        "assessment": {
            "available": True,
            "health": 0.9,
            "gaps": [],
            "objective": "observe",
        },
    }


def test_missing_shared_observation_fails_closed():
    assert build_factory_decision_context({}) == {
        "available": False,
        "interaction": {
            "correlation_rate": 1.0,
            "orphan_reply_count": 0,
            "single_event_count": 0,
            "task_thread_coverage": 0.0,
            "window_truncated": False,
        },
        "admission": {"available": False, "msg_id": None, "reply_to": None, "task_id": None, "admitted": False, "reason": None, "decided_at": None},
        "assessment": {"available": False, "health": None, "gaps": [], "objective": None},
    }
