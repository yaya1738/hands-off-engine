from autonomous.credentials.intelligence.event_bus import (
    IntelligenceEventBus,
)


def test_event_bus():

    bus = IntelligenceEventBus(
        "state/intelligence/test_events.jsonl"
    )

    event = bus.emit(
        "confidence_alert",
        {
            "level":
            "warning"
        }
    )

    records = bus.read()

    assert event["event_type"] == "confidence_alert"
    assert records[0]["mode"] == "read_only"
