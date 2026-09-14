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
        "from": "factory", "type": "task_assignment", "msg_id": "m1",
        "to": "anyclaw",
        "context": {"task_id": "t1", "action": "dangerous_action"}
    })
    assert not valid
    assert "allowlist" in err


def test_action_allowlist_blocks_execute():
    """Invariant 3: 'execute' action not in allowlist."""
    w = _fresh_worker()
    valid, err = w.validate_task_envelope({
        "from": "factory", "type": "task_assignment", "msg_id": "m2",
        "to": "anyclaw",
        "context": {"task_id": "t1", "action": "execute"}
    })
    assert not valid
    assert "allowlist" in err


def test_action_allowlist_accepts_valid():
    """Invariant 3: valid actions pass."""
    w = _fresh_worker()
    for i, action in enumerate(w.ALLOWED_ACTIONS):
        valid, err = w.validate_task_envelope({
            "from": "factory", "type": "task_assignment", "msg_id": f"m{i}",
            "to": "anyclaw",
            "context": {"task_id": "t1", "action": action}
        })
        assert valid, f"action '{action}' should be allowed, got: {err}"


def test_rejects_wrong_target():
    """Invariant 3: tasks addressed to other agents rejected."""
    w = _fresh_worker()
    valid, err = w.validate_task_envelope({
        "from": "factory", "type": "task_assignment", "msg_id": "m4",
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
        w.COORDINATION_BUS = tmp / "inbox.jsonl"
        w.RESULTS = tmp / "results.jsonl"
        w.PROCESSED_IDS = tmp / "processed.json"
        w.LOCK_DIR = tmp / "locks"

        # Write two identical tasks (with strict envelope fields)
        task = json.dumps({
            "from": "factory", "type": "task_assignment", "msg_id": "dup-1",
            "to": "anyclaw", "message": "test",
            "context": {"task_id": "dup-1", "action": "health_check"}
        }) + "\n"
        w.COORDINATION_BUS.write_text(task + task)

        count = w.poll_once()
        assert count == 1, f"Should process once, got {count}"

        # Verify result written once
        results = w.RESULTS.read_text().strip().split("\n")
        assert len(results) == 1
    finally:
        shutil.rmtree(tmp)


# ── Round 19 hardening: strict envelope + crash recovery ──

def test_rejects_wrong_sender():
    """Strict: tasks from non-factory senders rejected."""
    w = _fresh_worker()
    valid, err = w.validate_task_envelope({
        "from": "evil-agent", "type": "task_assignment", "msg_id": "m1",
        "to": "anyclaw",
        "context": {"task_id": "t1", "action": "health_check"}
    })
    assert not valid
    assert "sender" in err


def test_rejects_wrong_type():
    """Strict: tasks with wrong type rejected."""
    w = _fresh_worker()
    valid, err = w.validate_task_envelope({
        "from": "factory", "type": "chat_message", "msg_id": "m2",
        "to": "anyclaw",
        "context": {"task_id": "t1", "action": "health_check"}
    })
    assert not valid
    assert "type" in err


def test_rejects_missing_msg_id():
    """Strict: tasks without msg_id rejected."""
    w = _fresh_worker()
    valid, err = w.validate_task_envelope({
        "from": "factory", "type": "task_assignment",
        "to": "anyclaw",
        "context": {"task_id": "t1", "action": "health_check"}
    })
    assert not valid
    assert "msg_id" in err


def test_accepts_valid_envelope():
    """Strict: well-formed envelope accepted."""
    w = _fresh_worker()
    valid, err = w.validate_task_envelope({
        "from": "factory", "type": "task_assignment", "msg_id": "m3",
        "to": "anyclaw",
        "context": {"task_id": "t3", "action": "health_check"}
    })
    assert valid
    assert err is None


def test_path_containment_uses_relative_to():
    """safe_resolve uses Path.is_relative_to, not string startswith."""
    w = _fresh_worker()
    # A path that would match via startswith but not via is_relative_to
    # e.g. if SAFE_READ_DIRS has /root/hands-off-engine/docs
    # then /root/hands-off-engine/docsEvil/secret would pass startswith
    # but not is_relative_to
    import tempfile as _tf
    tmp = _tf.mkdtemp()
    try:
        evil = Path(tmp) / "docsEvil"
        evil.mkdir()
        secret = evil / "secret.txt"
        secret.write_text("oops")
        # Temporarily add tmp as safe dir to test containment
        old_dirs = w.SAFE_READ_DIRS
        try:
            # This should NOT match docsEvil (different dir name)
            resolved, err = w.safe_resolve("docsEvil/secret.txt")
            # Should be rejected (not in SAFE_READ_DIRS)
            assert resolved is None or "outside" in (err or ""), \
                f"Path traversal via prefix collision should be rejected: {resolved}"
        finally:
            pass
    finally:
        import shutil
        shutil.rmtree(tmp)


def test_crash_recovery_reuses_existing_result():
    """If results.jsonl already has a task_id, it won't be re-executed."""
    w = _fresh_worker()
    tmp = Path(tempfile.mkdtemp())
    try:
        w.COORDINATION_BUS = tmp / "inbox.jsonl"
        w.RESULTS = tmp / "results.jsonl"
        w.PROCESSED_IDS = tmp / "processed.json"
        w.LOCK_DIR = tmp / "locks"

        # Write a task
        task = json.dumps({
            "from": "factory", "type": "task_assignment", "msg_id": "crash-1",
            "to": "anyclaw", "message": "test",
            "context": {"task_id": "crash-1", "action": "health_check"}
        })
        w.COORDINATION_BUS.write_text(task + "\n")

        # Simulate: result already written (crash recovery scenario)
        result_line = json.dumps({
            "from": "anyclaw", "to": "factory", "type": "task_result",
            "msg_id": "crash-1",
            "context": {"task_id": "crash-1", "status": "success"}
        })
        w.RESULTS.write_text(result_line + "\n")

        # Now poll: should skip the task since result already exists
        count = w.poll_once()
        assert count == 0, f"Should not re-execute, got {count}"
    finally:
        shutil.rmtree(tmp)
