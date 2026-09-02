from pathlib import Path
import ast


SOURCE_PATH = Path("factory_autonomy_preflight.py")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def test_legacy_preflight_has_no_process_or_file_mutation_authority():
    imports = {
        alias.name
        for node in ast.walk(TREE)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    calls = {
        node.func.attr
        for node in ast.walk(TREE)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "subprocess" not in imports
    assert not {"system", "popen", "write_text", "unlink", "remove"} & calls


def test_legacy_preflight_fails_closed():
    namespace = {"__name__": "factory_autonomy_preflight_test", "__file__": str(SOURCE_PATH.resolve())}
    exec(compile(SOURCE, str(SOURCE_PATH), "exec"), namespace)
    result = namespace["run_stage"]("factory_capability_scanner.py")
    assert result["disabled"] is True
    assert "FactoryAuthorityGateway" in result["error"]
    assert namespace["load_outputs"]() == {}
