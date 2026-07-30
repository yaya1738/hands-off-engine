from ai.factory.routine_architect import (
    FactoryRoutineArchitect,
)


def test_design_and_generate():

    architect = FactoryRoutineArchitect()

    result = architect.design_routine(
        "protocol_bootstrap",
        "initialize factory protocols",
        [
            "discover",
            "register",
            "verify",
        ],
        [
            "protocol_lifecycle_manager",
        ],
    )

    assert result["designed"] is True

    generated = architect.generate_definition(
        "protocol_bootstrap"
    )

    assert generated["generated"] is True


def test_validate():

    architect = FactoryRoutineArchitect()

    architect.design_routine(
        "test",
        "testing",
        ["step"],
    )

    assert architect.validate_definition("test")["valid"] is True
