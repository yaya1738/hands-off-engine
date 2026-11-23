import ast
from pathlib import Path


def test_moonshot_metrics_never_infer_trading_authority_or_fake_financial_defaults():
    source = Path("autonomous/moonshot_loop.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "get_system_metrics"
    )

    assignments = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = node.value
                elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == "metrics":
                    key = target.slice.value if isinstance(target.slice, ast.Constant) else None
                    if isinstance(key, str):
                        assignments[key] = node.value

    assert isinstance(assignments["trading_enabled"], ast.Constant)
    assert assignments["trading_enabled"].value is False
    for key in ("monthly_burn", "ai_spend", "position_value"):
        value = assignments[key]
        assert isinstance(value, ast.Constant)
        assert value.value == 0

    # A balance threshold is not an authorization mechanism.
    assert not any(
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Subscript)
        and isinstance(node.left.value, ast.Name)
        and node.left.value.id == "metrics"
        and isinstance(node.left.slice, ast.Constant)
        and node.left.slice.value == "balance"
        for node in ast.walk(function)
    )
