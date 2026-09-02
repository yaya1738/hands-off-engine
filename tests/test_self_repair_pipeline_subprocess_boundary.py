import importlib


def test_self_repair_pipeline_is_fail_closed():
    module = importlib.import_module("factory_self_repair_pipeline")

    result = module.run_tool(["python", "worker.py", "safe goal; echo INJECTION"])

    assert result["success"] is False
    assert result["authority_required"] is True
    assert "FactoryAuthorityGateway" in result["stderr"]
