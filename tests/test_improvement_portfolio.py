from ai.factory.improvement_portfolio import (
    FactoryImprovementPortfolio,
)


def test_add():
    portfolio = FactoryImprovementPortfolio()

    result = portfolio.add(
        {
            "name": "recovery",
            "priority": 0.9,
        }
    )

    assert result["status"] == "PENDING"


def test_update():
    portfolio = FactoryImprovementPortfolio()

    portfolio.add(
        {
            "name": "recovery",
        }
    )

    result = portfolio.update(
        "recovery",
        {
            "status": "ACTIVE",
        },
    )

    assert result["status"] == "ACTIVE"


def test_prioritize():
    portfolio = FactoryImprovementPortfolio()

    portfolio.add(
        {
            "name": "low",
            "priority": 0.2,
        }
    )

    portfolio.add(
        {
            "name": "high",
            "priority": 0.9,
        }
    )

    result = portfolio.prioritize()

    assert result[0]["name"] == "high"


def test_active():
    portfolio = FactoryImprovementPortfolio()

    portfolio.add(
        {
            "name": "test",
            "status": "ACTIVE",
        }
    )

    assert len(portfolio.active()) == 1


def test_history():
    portfolio = FactoryImprovementPortfolio()

    portfolio.add(
        {
            "name": "test",
        }
    )

    assert len(portfolio.history()) == 1
