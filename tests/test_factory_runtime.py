from ai.factory.runtime import FactoryRuntime


def test_runtime_status():
    runtime = FactoryRuntime()

    result = runtime.status()

    assert result["status"] == "HEALTHY"


def test_runtime_dashboard():
    runtime = FactoryRuntime()

    result = runtime.view()

    assert "health" in result
    assert "components" in result


def test_runtime_runs_factory():
    runtime = FactoryRuntime()

    result = runtime.run(
        "runtime-001",
        "test integrated runtime",
    )

    assert result["execution"].status == "SUCCESS"
