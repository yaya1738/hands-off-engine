from ai.factory.runtime_governance import (
    FactoryRuntimeGovernance,
)


def build():
    return FactoryRuntimeGovernance()


def test_policy_check():
    engine = build()

    result = engine.check_policy(
        {}
    )

    assert result["policy_allowed"] is True


def test_permission_check():
    engine = build()

    result = engine.check_permission(
        {}
    )

    assert result["permission_allowed"] is True


def test_risk_check():
    engine = build()

    result = engine.assess_risk(
        {}
    )

    assert result["risk_checked"] is True


def test_authorize_execution():
    engine = build()

    result = engine.authorize_execution(
        {}
    )

    assert result["authorized"] is True


def test_audit_execution():
    engine = build()

    result = engine.audit_execution(
        {}
    )

    assert result["audited"] is True


def test_history():
    engine = build()

    engine.check_policy(
        {}
    )

    assert len(engine.history()) == 1
