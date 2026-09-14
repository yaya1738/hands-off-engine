import json, sys, os, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _fresh_worker():
    """Import worker with REPO_ROOT pointing to actual checkout."""
    import scripts.task_worker as w
    return w


def test_repo_root_derived_from_checkout():
    """Invariant 1: REPO_ROOT is the actual git checkout, not hardcoded."""
    w = _fresh_worker()
    assert (w.REPO_ROOT / ".git").exists(), "REPO_ROOT must be the git checkout root"
    assert "hands-off-engine" in str(w.REPO_ROOT)


def test_read_file_rejects_absolute_path():
    """Invariant 2a: absolute paths rejected."""
    w = _fresh_worker()
    resolved, err = w.safe_resolve("/etc/passwd")
    assert resolved is None
    assert "absolute" in err


def test_read_file_rejects_dotdot():
    """Invariant 2b: .. traversal rejected."""
    w = _fresh_worker()
    resolved, err = w.safe_resolve("../../etc/passwd")
    assert resolved is None
    assert ".." in err


def test_read_file_rejects_outside_safe_dirs():
    """Invariant 2c: paths outside safe dirs rejected."""
    w = _fresh_worker()
    resolved, err = w.safe_resolve(".env.polymarket")
    assert resolved is None
    assert "outside" in err


def test_read_file_accepts_safe_path():
    """Invariant 2d: safe paths within allowed dirs work."""
    w = _fresh_worker()
    resolved, err = w.safe_resolve("docs/ANYCLAW_HANDSHAKE_RESPONSE.json")
    assert resolved is not None
    assert err is None
    assert resolved.exists()


def test_action_allowlist_blocks_unknown():
    """Invariant 3: unknown actions rejected."""
    w = _fresh_worker()
    valid, err = w.validate_task_envelope({
        "to": "anyclaw",
        "context": {"task_id": "t1", "action": "dangerous_action"}
    })
    assert not valid
    assert "allowlist" in err


def test_action_allowlist_blocks_execute():
    """Invariant 3: 'execute' action not in allowlist."""
    w = _fresh_worker()
    valid, err = w.validate_task_envelope({
        "to": "anyclaw",
        "context": {"task_id": "t1", "action": "execute"}
    })
    assert not valid
    assert "allowlist" in err


def test_action_allowlist_accepts_valid():
    """Invariant 3: valid actions pass."""
    w = _fresh_worker()
    for action in w.ALLOWED_ACTIONS:
        valid, err = w.validate_task_envelope({
            "to": "anyclaw",
            "context": {"task_id": "t1", "action": action}
        })
        assert valid, f"action '{action}' should be allowed, got: {err}"


def test_rejects_wrong_target():
    """Invariant 3: tasks addressed to other agents rejected."""
    w = _fresh_worker()
    valid, err = w.validate_task_envelope({
        "to": "claude-code",
        "context": {"task_id": "t1", "action": "health_check"}
    })
    assert not valid


def test_no_git_push_in_worker():
    """Invariant 4: worker must not contain executable git push commands."""
    w = _fresh_worker()
    source = Path(w.__file__).read_text()
    # Check for subprocess calls containing push (not comments/docstrings)
    import ast
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "run":
                # It's a subprocess.run call — check args for "push"
                for arg in node.args:
                    if isinstance(arg, (ast.List, ast.Tuple)):
                        vals = [elt.value if isinstance(elt, ast.Constant) else "" for elt in arg.elts]
                        joined = " ".join(vals)
                        assert "push" not in joined, f"subprocess.run with push found: {joined}"
                    elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        assert "push" not in arg.value, f"push in subprocess arg: {arg.value}"


def test_duplicate_delivery_safety():
    """Invariant 5: same task_id processed only once."""
    w = _fresh_worker()
    tmp = Path(tempfile.mkdtemp())
    try:
        # Set up temp paths
        w.INBOX = tmp / "inbox.jsonl"
        w.RESULTS = tmp / "results.jsonl"
        w.PROCESSED_IDS = tmp / "processed.json"
        w.LOCK_DIR = tmp / "locks"

        # Write two identical tasks
        task = json.dumps({"to": "anyclaw", "message": "test", "context": {"task_id": "dup-1", "action": "health_check"}}) + "\n"
        w.INBOX.write_text(task + task)

        count = w.poll_once()
        assert count == 1, f"Should process once, got {count}"

        # Verify result written once
        results = w.RESULTS.read_text().strip().split("\n")
        assert len(results) == 1
    finally:
        shutil.rmtree(tmp)
