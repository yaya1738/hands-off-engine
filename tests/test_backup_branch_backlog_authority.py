from pathlib import Path
import ast
import re


ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "autonomous" / "backup_manager.py",
    ROOT / "integrafix" / "branch_consolidator.py",
    ROOT / "autonomous" / "backlog_scanner.py",
]


def _source(path):
    return path.read_text(encoding="utf-8")


def _calls(path):
    tree = ast.parse(_source(path))
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call)]


def test_legacy_operational_helpers_have_no_process_execution_or_mutation_imports():
    banned_imports = {"subprocess", "shutil", "os"}
    banned_calls = {"system", "popen", "remove", "unlink", "rmtree", "copy", "copy2", "move"}
    for path in TARGETS:
        tree = ast.parse(_source(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(alias.name.split(".")[0] in banned_imports for alias in node.names), path
            if isinstance(node, ast.ImportFrom):
                assert node.module not in banned_imports, path
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in banned_calls, (path, node.func.attr)


def test_backup_mutations_fail_closed():
    namespace = {"__file__": str(TARGETS[0])}
    exec(compile(_source(TARGETS[0]), str(TARGETS[0]), "exec"), namespace)
    manager = namespace["BackupManager"]()
    assert manager.backup_code_to_github() is False
    assert manager.backup_state_files() is False
    assert manager.backup_critical_data() == {"code": False, "state": False}


def test_branch_mutations_fail_closed():
    namespace = {"__file__": str(TARGETS[1])}
    exec(compile(_source(TARGETS[1]), str(TARGETS[1]), "exec"), namespace)
    manager = namespace["BranchConsolidator"]()
    assert manager.fetch_branches() == []
    assert manager.cleanup_stale_branches(dry_run=False) == []
    assert manager.status()["authority_required"] is True


def test_backlog_scanner_contains_no_credential_and_fails_closed():
    source = _source(TARGETS[2])
    assert not re.search(r"ghp_[A-Za-z0-9_\-]{20,}", source)
    assert "GITHUB_TOKEN" not in source
    namespace = {"__file__": str(TARGETS[2])}
    exec(compile(source, str(TARGETS[2]), "exec"), namespace)
    assert namespace["check_pr"](239) is None
    assert namespace["respond_to_action"](239, "comment", {}) is False
