from ai.factory.system_architect import (
    FactorySystemArchitect,
)


def test_design_system():

    architect = FactorySystemArchitect()

    result = architect.design_system(
        "requirement_generation_intake",
        "convert observations into requirements",
        [
            "intake",
            "normalization",
            "validation",
            "history",
        ],
        [
            "operations_intelligence",
        ],
    )

    assert result["designed"] is True


def test_generate_and_validate():

    architect = FactorySystemArchitect()

    architect.design_system(
        "test_system",
        "testing",
        [
            "component",
        ],
    )

    assert architect.generate_plan(
        "test_system"
    )["generated"] is True

    assert architect.validate_design(
        "test_system"
    )["valid"] is True
