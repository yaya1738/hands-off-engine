from ai.factory.decision_context import (
    FactoryDecisionContext,
)


def test_add_signal():
    context = FactoryDecisionContext()

    context.add_signal(
        "health",
        "DEGRADED",
    )

    result = context.build()

    assert result["health"] == "DEGRADED"


def test_multiple_signals():
    context = FactoryDecisionContext()

    context.add_signal(
        "risk",
        "LOW",
    )

    context.add_signal(
        "runtime",
        "ACTIVE",
    )

    result = context.build()

    assert result["risk"] == "LOW"
    assert result["runtime"] == "ACTIVE"


def test_snapshot():
    context = FactoryDecisionContext()

    context.add_signal(
        "test",
        True,
    )

    snapshot = context.snapshot()

    assert snapshot["signals"]["test"] is True
