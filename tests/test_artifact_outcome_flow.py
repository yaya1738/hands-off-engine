from ai.factory.runtime import FactoryRuntime


def test_runtime_creates_artifact():
    runtime = FactoryRuntime()

    runtime.execute(
        {
            "task": "artifact_registry_test"
        }
    )

    artifacts = runtime.artifact_registry.list_artifacts()

    assert len(artifacts) > 0
    assert artifacts[0]["status"] == "COMPLETED"
    assert "outcome" in artifacts[0]
    assert artifacts[0]["type"] == "development_proposal"
