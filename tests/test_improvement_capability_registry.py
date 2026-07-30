from ai.factory.improvement_capability_registry import (
    FactoryImprovementCapabilityRegistry,
)


def test_register_and_resolve():
    registry = FactoryImprovementCapabilityRegistry()

    def action():
        return "done"

    result = registry.register(
        "test_action",
        action,
    )

    assert result["registered"] is True
    assert registry.resolve("test_action")() == "done"


def test_status():
    registry = FactoryImprovementCapabilityRegistry()

    registry.register("one", lambda: True)

    assert registry.status()["count"] == 1
