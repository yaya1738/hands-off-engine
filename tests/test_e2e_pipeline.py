import json, sys, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.system_listener_inline import process_command
from scripts.control_api import SystemControl
from scripts.executor import Executor
from scripts.comm_hub import CommHub


def _make_workspace():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "state").mkdir()
    (tmp / "ai" / "coordination").mkdir(parents=True)
    (tmp / "state" / "inbound").mkdir()
    (tmp / "state" / "outbound").mkdir()
    return tmp


def _patch_module_paths(tmp):
    """Redirect module-level paths to temp workspace."""
    import scripts.system_listener_inline as listener
    import scripts.control_api as ctrl
    import scripts.executor as exec_mod
    import scripts.comm_hub as hub_mod

    orig = {
        'listener_state': listener.STATE_DIR,
        'listener_queue': listener.QUEUE_FILE,
        'listener_results': listener.RESULTS_FILE,
        'listener_approval': listener.APPROVAL_FILE,
    }

    listener.STATE_DIR = tmp / "state"
    listener.QUEUE_FILE = tmp / "state" / "command_queue.jsonl"
    listener.RESULTS_FILE = tmp / "state" / "results.jsonl"
    listener.APPROVAL_FILE = tmp / "state" / "approval_queue.json"

    exec_mod.EXECUTION_LOG = tmp / "state" / "execution_log.jsonl"
    exec_mod.RATE_LIMIT_FILE = tmp / "state" / "rate_limit_state.json"

    hub_mod.MESSAGES_FILE = tmp / "ai" / "coordination" / "messages.jsonl"
    hub_mod.COMM_LOG = tmp / "state" / "comm_log.jsonl"
    hub_mod.PARTY_REGISTRY = tmp / "state" / "party_registry.json"

    return orig


def _restore_module_paths(orig):
    import scripts.system_listener_inline as listener
    import scripts.executor as exec_mod
    import scripts.comm_hub as hub_mod

    listener.STATE_DIR = orig['listener_state']
    listener.QUEUE_FILE = orig['listener_queue']
    listener.RESULTS_FILE = orig['listener_results']
    listener.APPROVAL_FILE = orig['listener_approval']


def test_full_live_approval_execute():
    tmp = _make_workspace()
    orig = _patch_module_paths(tmp)
    try:
        # 1. Submit LIVE command to queue
        cmd = {"id": "e2e-1", "action": "execute", "mode": "LIVE",
               "payload": {"action": "trade", "params": {"market": "ETH-USD"}}, "status": "pending"}
        listener_ql = tmp / "state" / "command_queue.jsonl"
        listener_ql.write_text(json.dumps(cmd) + "\n")

        # 2. Listener processes → approval_required
        r1 = process_command(cmd)
        assert r1["command_status"] == "awaiting_approval"

        # 3. Operator approves
        appr = json.loads((tmp / "state" / "approval_queue.json").read_text())
        cmd_id = appr['pending'][0]['id']
        sc = SystemControl.__new__(SystemControl)
        sc.repo_root = tmp
        sc.state_dir = tmp / "state"
        sc.queue_file = listener_ql
        sc.results_file = tmp / "state" / "results.jsonl"
        sc.approval_file = tmp / "state" / "approval_queue.json"
        result = sc.approve(cmd_id)
        assert result["status"] == "approved"

        # 4. Queue entry has queued_at
        d = json.loads(listener_ql.read_text().strip())
        assert d["status"] == "pending"
        assert d["approval_status"] == "approved"
        assert "queued_at" in d

        # 5. Reprocess → executor runs
        r2 = process_command(d)
        assert r2["command_status"] == "executed"
        assert r2["execution_result"]["status"] == "executed"
    finally:
        _restore_module_paths(orig)
        shutil.rmtree(tmp)


def test_dryrun_needs_no_approval():
    tmp = _make_workspace()
    orig = _patch_module_paths(tmp)
    try:
        r = process_command({"id": "dr-1", "action": "execute", "mode": "DRYRUN",
                             "payload": {"action": "trade", "params": {}}})
        assert r.get("dryrun") is True
        # No approval queue entry
        assert not (tmp / "state" / "approval_queue.json").exists() or \
               len(json.loads((tmp / "state" / "approval_queue.json").read_text()).get("pending", [])) == 0
    finally:
        _restore_module_paths(orig)
        shutil.rmtree(tmp)


def test_reject_sacred_file():
    ex = Executor()
    result = ex.execute_command({
        "id": "sacred-1", "action": "execute", "mode": "LIVE",
        "approval_status": "approved",
        "queued_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "payload": {"action": "modify_file", "params": {"path": ".env.polymarket"}},
        "target": "executor",
    })
    assert result.status == "rejected"
    assert "sacred" in result.error.lower()


def test_rate_limit():
    import scripts.executor as ex_mod
    tmp = Path(tempfile.mkdtemp())
    (tmp / "state").mkdir()
    orig_rate = ex_mod.RATE_LIMIT_FILE
    orig_exec = ex_mod.EXECUTION_LOG
    ex_mod.RATE_LIMIT_FILE = tmp / "state" / "rate_limit_state.json"
    ex_mod.EXECUTION_LOG = tmp / "state" / "execution_log.jsonl"
    ex = Executor()
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    base = {"mode": "LIVE", "approval_status": "approved", "queued_at": now,
            "payload": {"action": "trade", "params": {"market": "BTC"}}, "target": "executor"}

    # Execute 10 commands (the limit)
    for i in range(10):
        r = ex.execute_command(dict(base, id=f"rate-{i}"))
        assert r.status == "executed", f"Command {i} should succeed"

    # 11th should be rate limited
    r11 = ex.execute_command(dict(base, id="rate-11"))
    assert r11.status == "rate_limited"

    # Cleanup
    ex_mod.RATE_LIMIT_FILE = orig_rate
    ex_mod.EXECUTION_LOG = orig_exec
    shutil.rmtree(tmp)
