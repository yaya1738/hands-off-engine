import ast
from pathlib import Path


def test_dass_heartbeat_is_bounded_module():
    source = Path("autonomous/dass_heartbeat.py").read_text()
    tree = ast.parse(source)
    names = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert "heartbeat" in names
