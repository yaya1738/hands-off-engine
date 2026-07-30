from ai.factory.workflow_orchestrator import (
    FactoryWorkflowOrchestrator,
)


def test_register_and_execute():

    workflow = FactoryWorkflowOrchestrator()

    workflow.register_step(
        "hello",
        lambda ctx: "done",
    )

    result = workflow.execute_workflow(
        ["hello"]
    )

    assert result["results"][0]["status"] == "COMPLETED"


def test_missing_step():

    workflow = FactoryWorkflowOrchestrator()

    result = workflow.execute_workflow(
        ["missing"]
    )

    assert result["results"][0]["status"] == "NO_HANDLER"
