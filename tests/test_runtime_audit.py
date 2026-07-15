from ai.factory.runtime_audit import (
    FactoryRuntimeAudit,
)


def test_record():
    audit = FactoryRuntimeAudit()

    result = audit.record(
        "DECISION",
        {
            "action": "IMPROVE",
        },
    )

    assert result["type"] == "DECISION"


def test_query():
    audit = FactoryRuntimeAudit()

    audit.record(
        "ACTION",
        {
            "name": "DEPLOY",
        },
    )

    result = audit.query(
        "ACTION"
    )

    assert len(result) == 1


def test_export():
    audit = FactoryRuntimeAudit()

    audit.record(
        "EVENT",
        {},
    )

    assert len(audit.export()) == 1


def test_history():
    audit = FactoryRuntimeAudit()

    audit.record(
        "EVENT",
        {},
    )

    assert len(audit.history()) == 1
