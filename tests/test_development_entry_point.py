from ai.factory.development_entry_point import (
    FactoryDevelopmentEntryPoint,
)


def test_entry_point_uses_architecture_context():

    factory = FactoryDevelopmentEntryPoint()

    result = factory.submit_objective(
        "improve runtime foundation",
        [
            "factory_runtime",
        ],
        [
            "lifecycle_coordination",
        ],
        architecture_context={
            "interfaces": [
                "runtime_api",
            ],
            "integration_points": [
                "FactoryRuntime",
            ],
            "verification_patterns": [
                "startup_test",
            ],
        },
    )

    spec = result["specification"]["specification"]

    assert result["status"] == "COMPLETE"
    assert "FactoryRuntime" in spec["integration_points"]
    assert "startup_test" in spec["verification_criteria"]


def test_history():

    factory = FactoryDevelopmentEntryPoint()

    factory.submit_objective(
        "test",
        ["a"],
        ["b"],
    )

    assert len(factory.history()) == 1
