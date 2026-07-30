from ai.factory.execution_handoff_adapter import (
    FactoryExecutionHandoffAdapter,
)


def test_create_handoff():
    adapter = FactoryExecutionHandoffAdapter()

    result = adapter.create_handoff(
        {
            "target": "FactoryExecutionIntelligence",
            "execution_requirements": [
                "create execution request",
            ],
            "verification_requirements": [
                "verify completion",
            ],
        }
    )

    assert result["created"] is True


def test_validate_handoff():
    adapter = FactoryExecutionHandoffAdapter()

    adapter.create_handoff(
        {
            "target": "execution",
            "execution_requirements": [],
            "verification_requirements": [],
        }
    )

    assert adapter.validate_handoff()["valid"] is True
