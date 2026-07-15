from ai.factory.recovery_management import (
    FactoryRecoveryManagement,
)


def build():
    return FactoryRecoveryManagement()


def test_detect_failure():
    manager = build()

    result = manager.detect_failure(
        {}
    )

    assert result["detected"] is True


def test_attempt_recovery():
    manager = build()

    result = manager.attempt_recovery(
        {}
    )

    assert result["attempted"] is True


def test_validate_recovery():
    manager = build()

    result = manager.validate_recovery(
        {}
    )

    assert result["validated"] is True


def test_record_incident():
    manager = build()

    result = manager.record_incident(
        {}
    )

    assert result["recorded"] is True


def test_history():
    manager = build()

    manager.detect_failure({})

    assert len(manager.history()) == 1
