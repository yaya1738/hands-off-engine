from ai.factory.development_pipeline import FactoryDevelopmentPipeline


def test_pipeline_exposes_bounded_executor():
    pipeline = FactoryDevelopmentPipeline()
    assert pipeline.executor.local_agent.agent is None
    result = pipeline.executor.execute({"id": "contract", "objective": "test"})
    assert result["status"] == "AGENT_UNAVAILABLE"
    assert result["allowed_paths"] == []
