import ast
from pathlib import Path


def test_dass_heartbeat_defines_heartbeat():
    source = Path("autonomous/dass_heartbeat.py").read_text()
    tree = ast.parse(source)
    assert any(isinstance(node, ast.FunctionDef) and node.name == "heartbeat" for node in tree.body)
