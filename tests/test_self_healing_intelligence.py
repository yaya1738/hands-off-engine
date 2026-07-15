from ai.factory.self_healing_intelligence import (
    FactorySelfHealingIntelligence,
)


def build():
    return FactorySelfHealingIntelligence()


def test_detect_failure():
    engine = build()

    result = engine.detect_failure(
        {}
    )

    assert result["detected"] is True


def test_diagnose_issue():
    engine = build()

    result = engine.diagnose_issue(
        {}
    )

    assert result["diagnosed"] is True


def test_apply_recovery():
    engine = build()

    result = engine.apply_recovery(
        {}
    )

    assert result["recovered"] is True


def test_verify_recovery():
    engine = build()

    result = engine.verify_recovery(
        {}
    )

    assert result["verified"] is True


def test_history():
    engine = build()

    engine.detect_failure(
        {}
    )

    assert len(engine.history()) == 1
