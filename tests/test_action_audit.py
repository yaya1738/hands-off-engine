from ai.factory.action_audit import (
    FactoryActionAudit,
)


def build():
    return FactoryActionAudit()


def test_record_action():
    audit = build()

    result = audit.record_action(
        {
            "action": "RUN",
        }
    )

    assert result["type"] == "ACTION"


def test_record_decision():
    audit = build()

    result = audit.record_decision(
        {}
    )

    assert result["type"] == "DECISION"


def test_record_outcome():
    audit = build()

    result = audit.record_outcome(
        {}
    )

    assert result["type"] == "OUTCOME"


def test_query():
    audit = build()

    audit.record_action({})

    result = audit.query(
        "ACTION"
    )

    assert len(result) == 1


def test_history():
    audit = build()

    audit.record_action({})

    assert len(audit.history()) == 1
