from ai.factory.routine_builder import (
    FactoryRoutineBuilder,
)


def test_create_routine():

    builder = FactoryRoutineBuilder()

    result = builder.create_routine(
        "protocol_bootstrap",
        "register factory protocols",
        [
            "collect",
            "register",
            "verify",
        ],
    )

    assert result["created"] is True


def test_execute_and_verify():

    builder = FactoryRoutineBuilder()

    builder.create_routine(
        "test",
        "testing",
        ["step"],
    )

    execution = builder.execute_routine("test")
    verification = builder.verify_routine("test")

    assert execution["executed"] is True
    assert verification["verified"] is True
