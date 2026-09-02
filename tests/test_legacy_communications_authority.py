import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["autonomous/pr_email_bridge.py", "autonomous/email_inbox_handler.py"]


def test_legacy_communication_targets_have_no_process_execution_or_embedded_token():
    for rel in TARGETS:
        text = (ROOT / rel).read_text()
        tree = ast.parse(text)
        assert "subprocess" not in text
        assert "GITHUB_TOKEN" not in text
        assert not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"system", "popen", "Popen", "check_call", "check_output"}
            for node in ast.walk(tree)
        )


def test_legacy_communication_boundaries_fail_closed():
    bridge = importlib.import_module("autonomous.pr_email_bridge")
    assert bridge.PREmailBridge().send_pr_comment(1, "example/repo", "x") is False
    assert bridge.PREmailBridge().monitor_and_respond() == 0

    handler = importlib.import_module("autonomous.email_inbox_handler")
    instance = handler.EmailInboxHandler()
    assert instance.connect_imap() is False
    assert instance.gh_comment(1, "x") is False
