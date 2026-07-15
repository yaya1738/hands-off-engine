from ai.factory.event_integration import (
    FactoryEventIntegration,
)


class FakeBus:
    def __init__(self):
        self.events = []

    def publish(
        self,
        event,
        payload,
    ):
        self.events.append(
            {
                "event": event,
                "payload": payload,
            }
        )

        return ["ok"]


def test_job_event():
    bus = FakeBus()

    integration = FactoryEventIntegration(
        bus
    )

    result = integration.emit_job_event(
        "job-1",
        "SUCCESS",
    )

    assert result == ["ok"]
    assert bus.events[0]["event"] == "JOB_COMPLETED"


def test_decision_event():
    bus = FakeBus()

    integration = FactoryEventIntegration(
        bus
    )

    integration.emit_decision_event(
        "CONTINUE",
        0.9,
    )

    assert bus.events[0]["payload"]["confidence"] == 0.9


def test_action_event():
    bus = FakeBus()

    integration = FactoryEventIntegration(
        bus
    )

    integration.emit_action_event(
        "OPTIMIZE",
    )

    assert bus.events[0]["event"] == "ACTION_EXECUTED"
