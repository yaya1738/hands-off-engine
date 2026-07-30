from ai.factory.component_design_pipeline import (
    FactoryComponentDesignPipeline,
)


def test_design_request_pipeline():

    pipeline = FactoryComponentDesignPipeline()

    result = pipeline.submit_design_request(
        need="create reusable system creation workflow",
        current_capabilities=[
            "component_design",
            "routine_creation",
        ],
        desired_outcome="coordinate system creation",
        component_name="system_creation_controller",
        purpose="coordinate creation of systems",
        responsibilities=[
            "receive specifications",
            "coordinate builders",
            "verify results",
        ],
        dependencies=[
            "system_architect",
        ],
    )

    assert result["design"]["designed"] is True
    assert result["validation"]["valid"] is True


def test_history():

    pipeline = FactoryComponentDesignPipeline()

    pipeline.submit_design_request(
        "test",
        ["existing"],
        "desired",
        "test_component",
        "testing",
        ["step"],
    )

    assert len(pipeline.history()) == 1
