from ai.factory.audit_intelligence import (
    FactoryAuditIntelligence,
)


def build():
    return FactoryAuditIntelligence()


def test_record_event():
    audit = build()

    result = audit.record_event(
        {}
    )

    assert result["recorded"] is True


def test_query_events():
    audit = build()

    result = audit.query_events(
        {}
    )

    assert result["queried"] is True


def test_verify_integrity():
    audit = build()

    result = audit.verify_integrity()

    assert result["verified"] is True


def test_generate_audit_report():
    audit = build()

    result = audit.generate_audit_report()

    assert result["generated"] is True


def test_history():
    audit = build()

    audit.record_event(
        {}
    )

    assert len(audit.history()) == 1
