from scripts.factory_decision_context import build_factory_decision_context


def test_learning_observation_is_bounded_and_preserved():
    snapshot = {
        "correlation_health": {"available": True, "event_count": 2, "correlated_event_count": 2},
        "learning_observation": {"available": True, "lifecycle_entry_count": 2, "completed_count": 2, "observed_count": 1, "outcome_count": 2, "success_count": 1, "failure_count": 1, "outcome_observation_rate": 0.5, "secret": "must not cross boundary"},
    }
    context = build_factory_decision_context(snapshot)
    assert context["learning"] == {"available": True, "lifecycle_entry_count": 2, "completed_count": 2, "observed_count": 1, "outcome_count": 2, "success_count": 1, "failure_count": 1, "outcome_observation_rate": 0.5}
    assert "secret" not in context["learning"]
    assert "execution_enabled" not in context["learning"]


def test_malformed_learning_observation_fails_closed():
    snapshot = {"correlation_health": {"available": True, "event_count": 1, "correlated_event_count": 1}, "learning_observation": "not-a-mapping"}
    context = build_factory_decision_context(snapshot)
    assert context["learning"] == {"available": False}
