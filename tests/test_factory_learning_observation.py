from scripts.factory_learning_observation import build_learning_observation


def test_learning_observation_summarizes_existing_outcomes():
    result = build_learning_observation(
        [
            {"states": {"completed": "t1", "observed": "t2"}},
            {"states": {"completed": "t3"}},
        ],
        [
            {"status": "success", "msg_id": "m1"},
            {"status": "failed", "msg_id": "m2"},
        ],
    )
    assert result["available"] is True
    assert result["completed_count"] == 2
    assert result["observed_count"] == 1
    assert result["success_count"] == 1
    assert result["failure_count"] == 1
    assert result["outcome_observation_rate"] == 0.5


def test_learning_observation_fails_closed_without_evidence():
    assert build_learning_observation([], []) == {"available": False}
