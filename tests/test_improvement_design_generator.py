from ai.factory.improvement_design_generator import (
    FactoryImprovementDesignGenerator,
)


def test_generates_engineering_specification():

    generator = FactoryImprovementDesignGenerator()

    result = generator.generate_specification(
        "runtime_lifecycle_coordinator",
        "coordinate Factory runtime lifecycle phases",
        [
            "manage startup",
            "coordinate execution phases",
        ],
        [
            "factory_runtime",
            "event_bus",
        ],
        category="runtime_component",
        problem="Factory lacks centralized lifecycle coordination",
        interfaces=[
            "runtime lifecycle API",
            "event interface",
        ],
        integration_points=[
            "FactoryRuntime",
            "ImprovementPipeline",
        ],
        data_requirements=[
            "component state",
        ],
        verification_criteria=[
            "startup test",
            "shutdown test",
        ],
        failure_modes=[
            "invalid lifecycle transition",
        ],
    )

    spec = result["specification"]

    assert result["generated"] is True
    assert spec["status"] == "SPECIFICATION_CREATED"
    assert spec["problem"] != ""
    assert spec["verification_criteria"]


def test_history():

    generator = FactoryImprovementDesignGenerator()

    generator.generate_specification(
        "test_component",
        "test",
        ["test"],
        [],
    )

    assert len(generator.history()) == 1
