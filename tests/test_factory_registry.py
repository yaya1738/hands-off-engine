from ai.factory.registry import FactoryRegistry


def test_register_component():
    registry = FactoryRegistry()

    registry.register(
        "planner",
        "planning",
        "1.0",
    )

    assert "planner" in registry.list_components()


def test_component_description():
    registry = FactoryRegistry()

    registry.register(
        "runner",
        "execution",
    )

    result = registry.describe("runner")

    assert result["type"] == "execution"
    assert result["version"] == "1.0"
