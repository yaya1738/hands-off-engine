from scripts.factory_learning_context import project_factory_learning_context


def test_learning_context_is_bounded_and_non_authoritative():
    result = project_factory_learning_context({
        "available": True,
        "lifecycle_entry_count": 4,
        "completed_count": 3,
        "observed_count": 2,
        "outcome_count": 3,
        "success_count": 2,
        "failure_count": 1,
        "outcome_observation_rate": 2 / 3,
        "secret": "do-not-copy",
        "execution_enabled": True,
    })
    assert result["available"] is True
    assert result["outcome_count"] == 3
    assert result["failure_count"] == 1
    assert "secret" not in result
    assert "execution_enabled" not in result


def test_unavailable_learning_fails_closed():
    assert project_factory_learning_context({"available": False}) == {"available": False}
