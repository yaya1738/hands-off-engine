from pathlib import Path
import ast


SOURCE_PATH = Path("factory_capability_constructor.py")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def test_legacy_capability_constructor_has_no_process_or_mutation_authority():
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


def test_legacy_capability_constructor_fails_closed():
    namespace = {"__name__": "factory_capability_constructor_test", "__file__": str(SOURCE_PATH.resolve())}
    exec(compile(SOURCE, str(SOURCE_PATH), "exec"), namespace)
    result = namespace["run_tool"]("factory_forensic_engine.py")
    assert result["success"] is False
    assert "FactoryAuthorityGateway" in result["error"]

    report = namespace["build_capability"]("test capability")
    assert report["decision"]["disabled"] is True
    assert report["decision"]["next_step"] == "FactoryAuthorityGateway"
    assert report["tools"] == []
