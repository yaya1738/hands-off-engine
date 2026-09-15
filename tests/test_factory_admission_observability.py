from scripts.factory_admission_observability import project_admission_observation


def test_projects_bounded_admission_observation():
    snapshot = {
        "admission_observation": {
            "available": True,
            "msg_id": "msg-1",
            "reply_to": "msg-1",
            "task_id": "task-1",
            "admitted": True,
            "reason": "accepted",
            "decided_at": "2026-09-15T06:00:00Z",
            "secret": "must-not-escape",
        }
    }

    assert project_admission_observation(snapshot) == {
        "available": True,
        "msg_id": "msg-1",
        "reply_to": "msg-1",
        "task_id": "task-1",
        "admitted": True,
        "reason": "accepted",
        "decided_at": "2026-09-15T06:00:00Z",
    }


def test_missing_observation_fails_closed():
    assert project_admission_observation({}) == {"available": False}
