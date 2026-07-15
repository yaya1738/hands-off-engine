from ai.factory.improvement_audit import (
    FactoryImprovementAudit,
)


def test_record():
    audit = FactoryImprovementAudit()

    result = audit.record(
        {
            "action": "restart",
            "result": "EXECUTED",
        }
    )

    assert result["action"]["action"] == "restart"


def test_query():
    audit = FactoryImprovementAudit()

    audit.record(
        {
            "action": "restart",
            "result": "EXECUTED",
        }
    )

    result = audit.query(
        "result",
        "EXECUTED",
    )

    assert len(result) == 1


def test_history():
    audit = FactoryImprovementAudit()

    audit.record(
        {
            "action": "test",
        }
    )

    assert len(audit.history()) == 1
