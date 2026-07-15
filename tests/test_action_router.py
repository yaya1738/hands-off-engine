from ai.factory.action_router import (
    FactoryActionRouter,
)


def test_route_recovery():
    router = FactoryActionRouter()

    router.register_handler(
        "RECOVER",
        lambda: "restarted",
    )

    result = router.route(
        {
            "decision": "RECOVER",
        }
    )

    assert result["status"] == "ROUTED"
    assert result["output"] == "restarted"


def test_missing_handler():
    router = FactoryActionRouter()

    result = router.route(
        {
            "decision": "UNKNOWN",
        }
    )

    assert result["status"] == "NO_HANDLER"


def test_history():
    router = FactoryActionRouter()

    router.route(
        {
            "decision": "UNKNOWN",
        }
    )

    assert len(router.history()) == 1
