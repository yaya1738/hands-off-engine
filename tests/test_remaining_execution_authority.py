import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    "termux-hands-off/agent/daily_summary.py",
    "factory_completion_authority_discovery.py",
    "factory_registration_contract_resolver.py",
    "factory_construction_autonomy_controller.py",
    "factory_completion_registration_resolver.py",
]


def test_targets_have_no_direct_process_execution():
    for rel in TARGETS:
        text = (ROOT / rel).read_text()
        tree = ast.parse(text)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_from = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert "subprocess" not in imported
        assert "subprocess" not in imported_from
        assert not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"system", "popen", "Popen", "check_call", "check_output"}
            for node in ast.walk(tree)
        )


def test_remaining_legacy_boundaries_are_disabled():
    daily = importlib.import_module("termux-hands-off.agent.daily_summary")
    assert daily.notify("x")["success"] is False

    modules = [
        "factory_completion_authority_discovery",
        "factory_registration_contract_resolver",
        "factory_construction_autonomy_controller",
        "factory_completion_registration_resolver",
    ]
    for name in modules:
        module = importlib.import_module(name)
        result = module.run()
        assert result["disabled"] is True
        assert result["authority"] == "FactoryAuthorityGateway"
