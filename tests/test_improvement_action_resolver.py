from ai.factory.improvement_action_resolver import (
    FactoryImprovementActionResolver,
)


def test_register_and_resolve():
    resolver = FactoryImprovementActionResolver()

    def handler():
        return "ok"

    resolver.register_action(
        "TEST",
        handler,
    )

    result = resolver.resolve(
        {
            "action": "TEST"
        }
    )

    assert result is handler


def test_missing_action_returns_none():
    resolver = FactoryImprovementActionResolver()

    result = resolver.resolve(
        {
            "action": "UNKNOWN"
        }
    )

    assert result is None
