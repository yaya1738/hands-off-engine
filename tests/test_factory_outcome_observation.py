from scripts.factory_outcome_observation import project_factory_outcome


def test_outcome_observation_projects_explicit_lifecycle_state():
    result = project_factory_outcome(
        {
            "task_id": "t-1",
            "msg_id": "m-2",
            "reply_to": "m-1",
            "status": "completed",
            "states": {"completed": "2026-09-17T15:00:00+00:00", "result_published": "2026-09-17T15:00:01+00:00", "observed": "2026-09-17T15:00:02+00:00"},
            "secret": "excluded",
        }
    )
    assert result["available"] is True
    assert result["task_id"] == "t-1"
    assert result["msg_id"] == "m-2"
    assert result["reply_to"] == "m-1"
    assert result["completed"] is True
    assert result["result_published"] is True
    assert result["observed"] is True
    assert "secret" not in result


def test_missing_lifecycle_identity_fails_closed():
    assert project_factory_outcome({"states": {"completed": "now"}})["available"] is False


def test_malformed_input_fails_closed():
    assert project_factory_outcome(None) == {"available": False}
