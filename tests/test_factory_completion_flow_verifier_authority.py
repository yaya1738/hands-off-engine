from pathlib import Path
import ast


SOURCE_PATH = Path("factory_completion_flow_verifier.py")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def test_legacy_completion_verifier_has_no_process_execution():
    imports = {
        alias.name
        for node in ast.walk(TREE)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "subprocess" not in imports


def test_legacy_completion_verifier_fails_closed():
    namespace = {"__name__": "factory_completion_flow_verifier_test", "__file__": str(SOURCE_PATH.resolve())}
    exec(compile(SOURCE, str(SOURCE_PATH), "exec"), namespace)
    result = namespace["run_controller"]()
    assert result["disabled"] is True
    assert "FactoryAuthorityGateway" in result["error"]
    decision = namespace["run"]()["decision"]
    assert decision["disabled"] is True
    assert decision["next_step"] == "FactoryAuthorityGateway"
