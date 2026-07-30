from ai.factory.routine_creation_pipeline import (
    FactoryRoutineCreationPipeline,
)


def test_create_from_requirement():

    pipeline = FactoryRoutineCreationPipeline()

    result = pipeline.create_from_requirement(
        "create protocol bootstrap routine",
        "protocol_bootstrap",
        "initialize factory protocols",
        [
            "discover",
            "register",
            "verify",
        ],
    )

    assert result["created"] is True
    assert result["verification"]["valid"] is True


def test_history():

    pipeline = FactoryRoutineCreationPipeline()

    pipeline.create_from_requirement(
        "test",
        "test_routine",
        "testing",
        ["step"],
    )

    assert len(pipeline.history()) == 1
