import json
from datetime import datetime, timezone

import pytest

from scripts.control_api import SystemControl
from scripts.executor import Executor
import scripts.executor as executor_module


def _approved_command(tmp_path):
    control = SystemControl(repo_root=tmp_path)
    command_id = control.submit_command(
        action="execute", target="executor",
        payload={"action": "trade", "params": {"market": "BTC", "amount": 10}},
        mode="LIVE", sync=False,
    )
    queued_at = datetime.now(timezone.utc).isoformat()
    queue = {
        "pending": [{
            "id": command_id, "action": "execute", "target": "executor",
            "payload": {"action": "trade", "params": {"market": "BTC", "amount": 10}},
            "mode": "LIVE", "queued_at": queued_at,
        }],
        "approved": [], "rejected": [],
    }
    control.approval_file.write_text(json.dumps(queue), encoding="utf-8")
    assert control.approve(command_id)["status"] == "approved"
    command = json.loads(control.queue_file.read_text(encoding="utf-8").splitlines()[0])
    return control, command


def _patch_executor_logs(tmp_path, monkeypatch):
    monkeypatch.setattr(executor_module, "EXECUTION_LOG", tmp_path / "state" / "execution_log.jsonl")
    monkeypatch.setattr(executor_module, "RATE_LIMIT_FILE", tmp_path / "state" / "rate_limit_state.json")


def test_live_command_payload_mutation_after_approval_is_rejected(tmp_path, monkeypatch):
    _patch_executor_logs(tmp_path, monkeypatch)
    control, command = _approved_command(tmp_path)
    command["payload"]["params"]["amount"] = 900
    executor = Executor(repo_root=tmp_path)
    result = executor.execute_command(command)
    assert result.status == "rejected"
    assert "changed after approval" in result.error
    assert not (tmp_path / "state" / "execution_claims").exists()


def test_live_command_approval_is_claimed_only_once(tmp_path, monkeypatch):
    _patch_executor_logs(tmp_path, monkeypatch)
    _, command = _approved_command(tmp_path)
    executor = Executor(repo_root=tmp_path)
    calls = []
    executor._live_execute = lambda _cmd: calls.append(1) or executor._dryrun_execute(_cmd)
    first = executor.execute_command(command)
    second = executor.execute_command(command)
    assert len(calls) == 1
    assert first.status == "dryrun"
    assert second.status == "rejected"
    assert "already claimed" in second.error


def test_live_execution_claim_survives_process_crash(tmp_path, monkeypatch):
    _patch_executor_logs(tmp_path, monkeypatch)
    _, command = _approved_command(tmp_path)
    executor = Executor(repo_root=tmp_path)
    def crash(_cmd):
        raise SystemExit("simulated process death after claim")
    executor._live_execute = crash
    with pytest.raises(SystemExit):
        executor.execute_command(command)
    retry = Executor(repo_root=tmp_path).execute_command(command)
    assert retry.status == "rejected"
    assert "already claimed" in retry.error


def test_approval_requires_exactly_one_matching_command(tmp_path):
    control = SystemControl(repo_root=tmp_path)
    command_id = control.submit_command(
        action="execute", target="executor", payload={"action": "trade", "params": {}},
        mode="LIVE", sync=False,
    )
    control.approval_file.write_text(json.dumps({
        "pending": [{"id": command_id, "action": "execute", "target": "executor",
                     "payload": {"action": "trade", "params": {}}, "mode": "LIVE",
                     "queued_at": datetime.now(timezone.utc).isoformat()}],
        "approved": [], "rejected": [],
    }), encoding="utf-8")
    with control.queue_file.open("a", encoding="utf-8") as handle:
        handle.write(control.queue_file.read_text(encoding="utf-8"))
    result = control.approve(command_id)
    assert result["status"] == "error"
    assert "exactly one" in result["error"]


def test_two_executor_instances_cannot_claim_same_live_approval(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    import time
    _patch_executor_logs(tmp_path, monkeypatch)
    _, command = _approved_command(tmp_path)
    first_executor = Executor(repo_root=tmp_path)
    second_executor = Executor(repo_root=tmp_path)
    calls = []
    calls_lock = threading.Lock()
    def perform(_cmd):
        with calls_lock:
            calls.append(1)
        time.sleep(0.05)
        return first_executor._dryrun_execute(_cmd)
    first_executor._live_execute = perform
    second_executor._live_execute = perform
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda ex: ex.execute_command(command), [first_executor, second_executor]))
    assert len(calls) == 1
    assert sum(result.status == "dryrun" for result in results) == 1
    assert sum(result.status == "rejected" for result in results) == 1
