from ai.factory.audit_trail import (
    FactoryAuditTrail,
)


def build():
    return FactoryAuditTrail()


def test_record_action():
    audit = build()

    result = audit.record_action(
        {
            "action": "RUN",
        }
    )

    assert result["recorded"] is True


def test_record_decision():
    audit = build()

    result = audit.record_decision(
        {
            "decision": "APPROVE",
        }
    )

    assert result["recorded"] is True


def test_query_records():
    audit = build()

    audit.record_action({})

    result = audit.query_records(
        "action"
    )

    assert len(result["records"]) == 1


def test_verify_integrity():
    audit = build()

    result = audit.verify_integrity()

    assert result["valid"] is True


def test_history():
    audit = build()

    audit.record_action({})

    assert len(audit.history()) == 1
