from ai.factory.risk_management import (
    FactoryRiskManagement,
)


def build():
    return FactoryRiskManagement()


def test_assess_risk():
    risk = build()

    result = risk.assess_risk(
        {
            "action": "RUN",
        }
    )

    assert result["risk_assessed"] is True


def test_calculate_exposure():
    risk = build()

    result = risk.calculate_exposure(
        {}
    )

    assert result["exposure_calculated"] is True


def test_approve_action():
    risk = build()

    result = risk.approve_action(
        {}
    )

    assert result["approved"] is True


def test_reject_action():
    risk = build()

    result = risk.reject_action(
        {}
    )

    assert result["rejected"] is True


def test_history():
    risk = build()

    risk.assess_risk({})

    assert len(risk.history()) == 1
