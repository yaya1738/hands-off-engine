from ai.factory.audit_log import (
    FactoryAuditLog,
)


def test_record_event():
    audit = FactoryAuditLog()

    event = audit.record_event(
        "ACTION",
        {
            "action": "OPTIMIZE",
        },
    )

    assert event["type"] == "ACTION"
    assert event["data"]["action"] == "OPTIMIZE"


def test_list_events():
    audit = FactoryAuditLog()

    audit.record_event(
        "TEST",
        {},
    )

    assert len(audit.list_events()) == 1


def test_filter_events():
    audit = FactoryAuditLog()

    audit.record_event(
        "DECISION",
        {},
    )

    audit.record_event(
        "ACTION",
        {},
    )

    result = audit.filter_events(
        "ACTION"
    )

    assert len(result) == 1
