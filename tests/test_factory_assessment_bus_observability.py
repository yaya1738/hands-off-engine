from scripts.factory_assessment_observability import latest_factory_assessment


def test_latest_factory_assessment_uses_explicit_bus_event_only():
    events = [
        {"type": "factory.assessment", "payload": {"assessment": {"health": 0.5, "gaps": ["old"]}}},
        {"type": "other.event", "payload": {"assessment": {"health": 0.1}}},
        {"type": "factory.assessment", "payload": {"assessment": {"health": 0.9, "gaps": ["new"], "objective": "improve", "interaction_health": {"available": True}}}},
    ]

    assert latest_factory_assessment(events) == {
        "available": True,
        "health": 0.9,
        "gaps": ["new"],
        "objective": "improve",
        "interaction_health": {"available": True},
    }


def test_factory_assessment_bus_projection_fails_closed():
    assert latest_factory_assessment([]) == {"available": False}
    assert latest_factory_assessment([{"type": "factory.assessment", "payload": {}}]) == {"available": False}


def test_factory_assessment_bus_projection_does_not_expose_extra_fields():
    events = [{
        "type": "factory.assessment",
        "payload": {"assessment": {
            "health": 1.0,
            "gaps": [],
            "objective": "safe",
            "interaction_health": {},
            "secret": "must-not-cross-boundary",
        }},
    }]

    result = latest_factory_assessment(events)
    assert "secret" not in result
    assert result["health"] == 1.0
