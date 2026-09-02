import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_bounty_monitor_has_no_process_or_embedded_credential_authority():
    text = (ROOT / "autonomous/bounty_monitor.py").read_text()
    tree = ast.parse(text)
    assert "subprocess" not in text
    assert "GITHUB_TOKEN" not in text
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"system", "popen", "Popen", "check_call", "check_output"}
        for node in ast.walk(tree)
    )
    module = importlib.import_module("autonomous.bounty_monitor")
    assert module.monitor_all_prs()["disabled"] is True
    assert module.respond_to_pr_comment(1, "example/repo", "x") is False


def test_auto_identity_is_fail_closed():
    text = (ROOT / "security/auto_identity.py").read_text()
    tree = ast.parse(text)
    assert "subprocess" not in text
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"system", "popen", "Popen", "check_call", "check_output"}
        for node in ast.walk(tree)
    )
    module = importlib.import_module("security.auto_identity")
    result = module.is_yair()
    assert result["is_master"] is False
    assert result["disabled"] is True
    assert module.am_i_yair() is False
