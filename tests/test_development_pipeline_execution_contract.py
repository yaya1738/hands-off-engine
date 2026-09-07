from ai.factory.development_pipeline import FactoryDevelopmentPipeline


class _UnavailableAgent:
    pass


def test_pipeline_reports_agent_unavailable_as_failed_execution():
    pipeline = FactoryDevelopmentPipeline()
    result = pipeline.run_development_cycle({"objective": "test bounded autonomous development"})

    assert result["execution"]["status"] == "AGENT_UNAVAILABLE"
    assert result["status"] == "agent_unavailable"
    assert result["execution_succeeded"] is False


def test_pipeline_reports_completed_agent_as_ready_for_review():
    def agent(_envelope):
        return {
            "status": "agent_completed",
            "response": {"status": "ready_for_review", "changed_files": []},
        }

    pipeline = FactoryDevelopmentPipeline(local_agent=agent)
    result = pipeline.run_development_cycle({"objective": "test completed autonomous development"})

    assert result["execution"]["status"] == "agent_completed"
    assert result["status"] == "ready_for_review"
    assert result["execution_succeeded"] is True
