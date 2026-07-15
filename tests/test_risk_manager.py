from ai.factory.risk_manager import (
    FactoryRiskManager,
)


def build():
    return FactoryRiskManager()


def test_assess():
    manager = build()

    result = manager.assess(
        {
            "action": "RUN",
        }
    )

    assert result["risk_score"] == 0


def test_constraints():
    manager = build()

    result = manager.check_constraints(
        {}
    )

    assert result["within_constraints"] is True


def test_approve():
    manager = build()

    result = manager.approve(
        {}
    )

    assert result["approved"] is True


def test_mitigate():
    manager = build()

    result = manager.mitigate(
        {}
    )

    assert result["mitigated"] is True


def test_history():
    manager = build()

    manager.assess({})

    assert len(manager.history()) == 1
