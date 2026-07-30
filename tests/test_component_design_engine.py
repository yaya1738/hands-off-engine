from ai.factory.component_design_engine import (
    FactoryComponentDesignEngine,
)


def test_design_component():

    engine = FactoryComponentDesignEngine()

    result = engine.design_component(
        "system_creation_controller",
        "create systems through repeatable workflows",
        [
            "receive requirements",
            "coordinate creation",
            "verify outcomes",
        ],
        [
            "system_architect",
        ],
    )

    assert result["designed"] is True


def test_spec_and_validation():

    engine = FactoryComponentDesignEngine()

    engine.design_component(
        "test_component",
        "testing",
        [
            "step",
        ],
    )

    assert engine.generate_specification(
        "test_component"
    )["generated"] is True

    assert engine.validate_design(
        "test_component"
    )["valid"] is True
