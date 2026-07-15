from ai.factory.self_healing import (
    FactorySelfHealing,
)


def build():
    return FactorySelfHealing()


def test_detect_failure():
    healer = build()

    result = healer.detect_failure(
        {
            "error": "TIMEOUT",
        }
    )

    assert result["detected"] is True


def test_diagnose_issue():
    healer = build()

    result = healer.diagnose_issue(
        {}
    )

    assert result["diagnosed"] is True


def test_repair_component():
    healer = build()

    result = healer.repair_component(
        {
            "name": "SERVICE",
        }
    )

    assert result["repaired"] is True


def test_verify_recovery():
    healer = build()

    result = healer.verify_recovery(
        {}
    )

    assert result["verified"] is True


def test_history():
    healer = build()

    healer.detect_failure({})

    assert len(healer.history()) == 1
