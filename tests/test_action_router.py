from ai.factory.action_router import (
    FactoryActionRouter,
)


def test_recovery_route():
    router = FactoryActionRouter()

    result = router.route(
        {
            "decision": "RECOVER",
        }
    )

    assert result["action"] == "runtime_recovery"


def test_improvement_route():
    router = FactoryActionRouter()

    result = router.route(
        {
            "decision": "IMPROVE",
        }
    )

    assert result["action"] == "improvement_pipeline"


def test_continue_route():
    router = FactoryActionRouter()

    result = router.route(
        {
            "decision": "CONTINUE",
        }
    )

    assert result["action"] == "continue"


def test_history():
    router = FactoryActionRouter()

    router.route(
        {
            "decision": "CONTINUE",
        }
    )

    assert len(router.history()) == 1
