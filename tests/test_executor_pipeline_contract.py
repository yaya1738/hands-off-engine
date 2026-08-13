from ai.factory.development_pipeline import FactoryDevelopmentPipeline


def test_pipeline_uses_explicit_bounded_executor():
    pipeline = FactoryDevelopmentPipeline()
    result = pipeline.executor.execute({"id": "contract", "objective": "test"})
    assert result["status"] == "AGENT_UNAVAILABLE"
    assert result["allowed_paths"] == []
