from ai.factory.compliance_audit import (
    FactoryComplianceAudit,
)


def build():
    return FactoryComplianceAudit()


def test_record_action():
    audit = build()

    result = audit.record_action(
        {
            "action": "RUN",
        }
    )

    assert result["status"] == "RECORDED"


def test_verify_compliance():
    audit = build()

    result = audit.verify_compliance(
        {}
    )

    assert result["compliant"] is True


def test_generate_report():
    audit = build()

    audit.record_action({})

    result = audit.generate_report()

    assert result["records"] == 1


def test_flag_violation():
    audit = build()

    result = audit.flag_violation(
        {}
    )

    assert result["flagged"] is True


def test_history():
    audit = build()

    audit.record_action({})

    assert len(audit.history()) == 1
