from ai.factory.decision_engine import FactoryDecisionEngine


def test_healthy_factory_continues():
    engine = FactoryDecisionEngine()

    result = engine.analyze(
        {
            "status": "HEALTHY",
        },
        [],
        {
            "failed": 0,
        },
    )

    assert result["action"] == "continue"


def test_failure_triggers_review():
    engine = FactoryDecisionEngine()

    result = engine.analyze(
        {
            "status": "HEALTHY",
        },
        [],
        {
            "failed": 2,
        },
    )

    assert result["action"] == "review_failures"


def test_unhealthy_factory_investigates():
    engine = FactoryDecisionEngine()

    result = engine.analyze(
        {
            "status": "DEGRADED",
        },
        [],
        {},
    )

    assert result["action"] == "investigate"
