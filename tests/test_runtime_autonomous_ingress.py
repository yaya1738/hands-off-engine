import ast
from pathlib import Path


RUNTIME = Path("ai/factory/runtime.py")


def _method(name):
    tree = ast.parse(RUNTIME.read_text(encoding="utf-8"))
    return next(
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    )


def test_autonomous_execute_delegates_to_authority_gateway():
    source = ast.get_source_segment(RUNTIME.read_text(encoding="utf-8"), _method("autonomous_execute"))
    assert source is not None
    assert "FactoryAuthorityGateway" in source
    assert ".execute_autonomous(" in source
    assert "FactoryRuntimeAutonomyGateway" not in source


def test_autonomous_execute_has_no_direct_runtime_execute_call():
    method = _method("autonomous_execute")
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "execute"
        for node in ast.walk(method)
    )
