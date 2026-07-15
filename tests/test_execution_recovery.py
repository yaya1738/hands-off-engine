from ai.factory.execution_recovery import (
    FactoryExecutionRecovery,
)


def build():
    return FactoryExecutionRecovery()


def test_detect_failure():
    recovery = build()

    result = recovery.detect_failure(
        {
            "status": "FAILED",
        }
    )

    assert result["failure_detected"] is True


def test_retry():
    recovery = build()

    result = recovery.retry({})

    assert result["retried"] is True


def test_recover():
    recovery = build()

    result = recovery.recover({})

    assert result["recovered"] is True


def test_escalate():
    recovery = build()

    result = recovery.escalate({})

    assert result["escalated"] is True


def test_history():
    recovery = build()

    recovery.retry({})

    assert len(recovery.history()) == 1
