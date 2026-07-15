from ai.factory.action_router import (
    FactoryActionRouter,
)


def test_route_continue():
    router = FactoryActionRouter()

    router.register_action(
        "CONTINUE",
        lambda: "running",
    )

    result = router.route(
        {
            "decision": "CONTINUE",
        }
    )

    assert result["result"] == "running"


def test_unknown_action():
    router = FactoryActionRouter()

    result = router.route(
        {
            "decision": "MISSING",
        }
    )

    assert result["error"] == "unknown_action"


def test_history():
    router = FactoryActionRouter()

    router.register_action(
        "OPTIMIZE",
        lambda: "optimized",
    )

    router.route(
        {
            "decision": "OPTIMIZE",
        }
    )

    assert len(router.history()) == 1
