from ai.factory.assessment_bus_publisher import FactoryAssessmentBusPublisher


class FakeHub:
    def __init__(self):
        self.calls = []

    def send(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"status": "sent"}


def test_assessment_publisher_uses_canonical_hub_and_bounds_payload():
    hub = FakeHub()
    assessment = {
        "health": 0.9,
        "gaps": ["low interaction correlation"],
        "objective": "observe",
        "context": "secret-context",
        "interaction_health": {"available": True},
        "secret": "must-not-leak",
    }

    result = FactoryAssessmentBusPublisher(hub).publish(assessment)

    assert result == {"status": "sent"}
    assert len(hub.calls) == 1
    args, kwargs = hub.calls[0]
    assert args == (
        "system_internal",
        "factory.assessment",
        {
            "assessment": {
                "health": 0.9,
                "gaps": ["low interaction correlation"],
                "objective": "observe",
                "interaction_health": {"available": True},
            }
        },
    )
    assert kwargs == {"source": "factory"}
    assert "secret" not in args[2]["assessment"]
    assert "context" not in args[2]["assessment"]


def test_assessment_publisher_fails_closed_without_assessment():
    hub = FakeHub()
    result = FactoryAssessmentBusPublisher(hub).publish(None)

    assert result == {"status": "skipped", "reason": "assessment_unavailable"}
    assert hub.calls == []
