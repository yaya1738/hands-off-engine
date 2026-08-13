from ai.factory.development_pipeline import FactoryDevelopmentPipeline


def test_pipeline_can_inject_local_agent():
    pipeline = FactoryDevelopmentPipeline(
        local_agent=lambda envelope: {
            "status": "executed",
            "objective": envelope["task"]["objective"],
        }
    )
    result = pipeline.executor.execute({"id": "contract", "objective": "test"})
    assert result["status"] == "executed"
    assert result["objective"] == "test"
