from ai.factory.decision_context_observer import FactoryDecisionContextObserver


def test_observer_returns_bounded_context_copy():
    source = {
        "available": True,
        "interaction": {"correlation_rate": 1.0},
        "admission": {"msg_id": "m-1", "admitted": True},
        "assessment": {"health": 0.9},
    }
    observed = FactoryDecisionContextObserver(source).observe()

    assert observed == source
    assert observed is not source


def test_observer_fails_closed_without_context():
    assert FactoryDecisionContextObserver().observe() == {"available": False}
