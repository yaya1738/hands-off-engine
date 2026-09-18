#!/usr/bin/env python3
"""
Task Worker — hardened bidirectional protocol between Factory and AnyClaw.

Canonical transport is ai/coordination/messages.jsonl. The legacy
ai/tasks inbox is intentionally not used as a second coordination bus.

Security invariants enforced:
1. Repo root derived from actual checkout, not hardcoded path
2. read_file_fact rejects absolute paths, .. traversal, symlink escapes
3. Task envelope validated against action allowlist
4. No git push — result publication stays local
5. Atomic claim/lock prevents duplicate task re-execution
6. No secrets exposed, no live/protected execution enabled
"""

import json
import sys
import os
import time
import fcntl
import logging
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from scripts.continuation import ContinuationEmitter
except ImportError:
    ContinuationEmitter = None

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [TaskWorker] %(message)s')
log = logging.getLogger("TaskWorker")

REPO_ROOT = Path(__file__).resolve().parent.parent
COORDINATION_BUS = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
RESULTS = REPO_ROOT / "state" / "task_results.jsonl"
LOCK_DIR = REPO_ROOT / "state" / "task_locks"
PROCESSED_IDS = REPO_ROOT / "state" / "processed_task_ids.json"
PUBLISH_LOCK = REPO_ROOT / "state" / "task_result_publish.lock"

_emitter = None
def get_emitter():
    global _emitter
    if _emitter is None and ContinuationEmitter is not None:
        _emitter = ContinuationEmitter()
    return _emitter

ALLOWED_ACTIONS = frozenset({
    "health_check",
    "system_status",
    "read_file_fact",
    "list_backends",
    "list_parties",
    "bus_summary",
    "test_status",
    "lifecycle_summary",
    "factory_execute",
})

SAFE_READ_DIRS = frozenset({
    REPO_ROOT / "docs",
    REPO_ROOT / "ai",
    REPO_ROOT / "state",
    REPO_ROOT / "scripts",
    REPO_ROOT / "tests",
    REPO_ROOT / "config",
})


def load_processed():
    if PROCESSED_IDS.exists():
        try:
            return set(json.loads(PROCESSED_IDS.read_text()))
        except Exception:
            pass
    return set()


def save_processed(ids):
    PROCESSED_IDS.parent.mkdir(parents=True, exist_ok=True)
    tmp = PROCESSED_IDS.with_suffix(".tmp")
    tmp.write_text(json.dumps(sorted(ids)))
    tmp.replace(PROCESSED_IDS)


class TaskLock:
    """File-based lock to prevent duplicate task re-execution."""
    def __init__(self, task_id):
        self.lock_dir = LOCK_DIR
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.lock_dir / f"{task_id}.lock"
        self.fd = None

    def try_acquire(self):
        try:
            self.fd = open(self.lock_path, "w")
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fd.write(str(os.getpid()))
            self.fd.flush()
            return True
        except (IOError, OSError):
            if self.fd:
                self.fd.close()
                self.fd = None
            return False

    def release(self):
        if self.fd:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                self.fd.close()
            except Exception:
                pass
        try:
            self.lock_path.unlink(missing_ok=True)
        except Exception:
            pass


class PublishLock:
    """Process-safe lock around result deduplication plus canonical append."""
    def __init__(self):
        PUBLISH_LOCK.parent.mkdir(parents=True, exist_ok=True)
        self.fd = None

    def __enter__(self):
        self.fd = open(PUBLISH_LOCK, "w")
        fcntl.flock(self.fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.fd:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
            finally:
                self.fd.close()
                self.fd = None


def safe_resolve(file_path):
    """Resolve a file path safely — reject absolute, .., and symlink escapes."""
    if not file_path or not isinstance(file_path, str):
        return None, "empty path"
    if os.path.isabs(file_path):
        return None, f"absolute path rejected: {file_path}"
    if ".." in file_path.split("/") or ".." in file_path.split(os.sep):
        return None, f".. traversal rejected: {file_path}"
    try:
        resolved = (REPO_ROOT / file_path).resolve()
    except Exception as e:
        return None, f"resolution failed: {e}"
    resolved_abs = resolved.resolve()
    in_safe = any(resolved_abs.is_relative_to(d.resolve()) for d in SAFE_READ_DIRS)
    if not in_safe:
        return None, f"path outside safe directories: {file_path} -> {resolved}"
    try:
        if resolved.is_symlink():
            return None, f"symlink rejected: {file_path}"
    except Exception:
        pass
    return resolved, None


def validate_task_envelope(task):
    """Validate strict Factory→AnyClaw task envelope."""
    if not isinstance(task, dict):
        return False, "task is not a dict"
    if task.get("from", "") != "factory":
        return False, f"unexpected sender: {task.get('from')!r}"
    if task.get("type", "") != "task_assignment":
        return False, f"unexpected type: {task.get('type')!r}"
    if not task.get("msg_id"):
        return False, "missing msg_id"
    context = task.get("context")
    if not isinstance(context, dict):
        return False, "missing or invalid context"
    if not context.get("task_id"):
        return False, "missing task_id"
    action = context.get("action", "")
    if not action:
        return False, "missing action"
    if action not in ALLOWED_ACTIONS:
        return False, f"action '{action}' not in allowlist"
    if action == "factory_execute":
        mode = str(context.get("mode", "DRYRUN")).upper()
        if mode not in {"DRYRUN", "LIVE"}:
            return False, "factory_execute has unsupported execution mode"
        objective = context.get("objective") or (context.get("params") or {}).get("objective")
        if not objective:
            return False, "factory_execute missing objective"
        if mode == "LIVE" and context.get("approval_status") != "approved":
            return False, "factory_execute LIVE requires explicit approval"
    to_field = task.get("to", "")
    if to_field and to_field not in ("anyclaw", "all"):
        return False, f"task addressed to '{to_field}', not 'anyclaw'"
    return True, None


def process_task(task):
    task_id = task["context"]["task_id"]
    action = task["context"]["action"]
    params = task["context"].get("params", {})
    log.info(f"Processing task {task_id[:8]}... action={action}")
    try:
        if action == "health_check":
            result = {"status": "success", "result": {"health": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}}
        elif action == "system_status":
            result = {"status": "success", "result": {"system": "running", "authority": "fail_closed"}}
        elif action == "read_file_fact":
            file_path = params.get("file_path", "")
            resolved, err = safe_resolve(file_path)
            if err:
                result = {"status": "error", "error": f"Path rejected: {err}"}
            else:
                result_data = {"file_path": file_path, "file_exists": resolved.exists()}
                if resolved.exists():
                    result_data["file_size_bytes"] = resolved.stat().st_size
                    try:
                        content = resolved.read_text()[:5000]
                        result_data["content_preview"] = content[:200]
                        fact_q = params.get("fact", "")
                        if "runtime identity" in fact_q.lower() or "name" in fact_q.lower():
                            try:
                                data = json.loads(content)
                                ri = data.get("runtime_identity", data.get("response", {}).get("runtime_identity", {}))
                                result_data["fact_answer"] = ri.get("name", "unknown")
                            except Exception:
                                result_data["fact_answer"] = "Could not parse JSON"
                        else:
                            result_data["fact_answer"] = content[:100]
                    except Exception:
                        result_data["fact_answer"] = "Could not read file"
                result = {"status": "success", "result": result_data}
        elif action == "list_backends":
            from scripts.ai_connector import AIConnector
            ai = AIConnector()
            result = {"status": "success", "result": {k: v["name"] for k, v in ai.list_backends().items()}}
        elif action == "list_parties":
            from scripts.comm_hub import CommHub
            hub = CommHub(repo_root=REPO_ROOT)
            result = {"status": "success", "result": [p["id"] for p in hub.list_parties()]}
        elif action == "bus_summary":
            bus_file = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
            if bus_file.exists():
                from collections import Counter
                msgs = []
                for line in bus_file.read_text().splitlines():
                    if line.strip():
                        try: msgs.append(json.loads(line))
                        except: pass
                types = Counter(m.get("type", "?") for m in msgs)
                msg_ids = [m.get("msg_id") or m.get("event_id") for m in msgs]
                unique_ids = len(set(mid for mid in msg_ids if mid))
                result = {"status": "success", "result": {
                    "total": len(msgs),
                    "by_type": dict(types.most_common()),
                    "unique_ids": unique_ids,
                    "dedup_ratio": round(unique_ids / max(len(msgs), 1), 2),
                    "truncated": len(msgs) > 120,
                }}
            else:
                result = {"status": "error", "error": "Bus file not found"}
        elif action == "test_status":
            import subprocess
            try:
                r = subprocess.run(
                    [sys.executable, "-m", "pytest", "tests/",
                     "--ignore=tests/integration", "--ignore=tests/unit",
                     "--ignore=tests/test_alpha_pipeline.py", "-q", "--tb=no"],
                    capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=120
                )
                output = r.stdout.strip()
                passed = output.count(".") if "." in output else 0
                result = {"status": "success", "result": {
                    "exit_code": r.returncode,
                    "passed": passed,
                    "output_preview": output[:200],
                }}
            except subprocess.TimeoutExpired:
                result = {"status": "error", "error": "Test suite timed out (120s)"}
            except Exception as e:
                result = {"status": "error", "error": str(e)}
        elif action == "factory_execute":
            from scripts.factory_execution_adapter import execute_factory_command
            command = {
                "id": task_id,
                "mode": params.get("mode", task["context"].get("mode", "DRYRUN")),
                "approval_status": params.get("approval_status", task["context"].get("approval_status")),
                "objective": task["context"].get("objective") or params.get("objective"),
                "payload": params,
                "correlation_id": task["context"].get("reply_to") or task["context"].get("correlation_id") or task_id,
                "reply_to": task["context"].get("reply_to"),
            }
            factory_result = execute_factory_command(command, execution_gate=True)
            if factory_result.get("status") in {"completed", "dryrun_only"}:
                result = {"status": "success", "result": factory_result}
            else:
                result = {"status": "error", "error": factory_result.get("reason") or factory_result.get("error") or factory_result}
        elif action == "lifecycle_summary":
            lifecycle_file = REPO_ROOT / "state" / "task_lifecycle.json"
            if lifecycle_file.exists():
                lc = json.loads(lifecycle_file.read_text())
                states = {}
                for tid, entry in lc.items():
                    state = max((entry.get("states", {}).keys()), key=lambda s: entry["states"].get(s, ""), default="unknown")
                    states[state] = states.get(state, 0) + 1
                result = {"status": "success", "result": {
                    "total_tasks": len(lc),
                    "by_state": states,
                }}
            else:
                result = {"status": "success", "result": {"total_tasks": 0, "by_state": {}}}
        else:
            result = {"status": "error", "error": f"Action '{action}' not implemented"}
    except Exception as e:
        result = {"status": "error", "error": str(e)}

    return {
        "from": "anyclaw", "to": "factory", "type": "task_result",
        "message": f"Result for {action}: {result.get('status', 'unknown')}",
        "msg_id": task_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": {
            "task_id": task_id,
            "status": result.get("status", "error"),
            "result": result.get("result"),
            "error": result.get("error"),
            "reply_to": task.get("context", {}).get("reply_to"),
        },
    }


def _publish_result_to_bus(result):
    """Publish one task_result to the canonical bus, idempotently by task_id."""
    task_id = (result.get("context") or {}).get("task_id") or result.get("msg_id")
    if not task_id:
        raise ValueError("task_result missing task_id")
    COORDINATION_BUS.parent.mkdir(parents=True, exist_ok=True)
    with PublishLock():
        existing_ids = set()
        if COORDINATION_BUS.exists():
            with COORDINATION_BUS.open("r") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        message = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    context = message.get("context") or {}
                    if message.get("type") == "task_result":
                        existing = context.get("task_id") or message.get("msg_id")
                        if existing:
                            existing_ids.add(existing)
        if task_id in existing_ids:
            return False
        with COORDINATION_BUS.open("a") as handle:
            handle.write(json.dumps(result, default=str) + "\n")
        return True


def _load_result_ids():
    result_ids = set()
    if RESULTS.exists():
        try:
            with open(RESULTS, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            r = json.loads(line)
                            tid = r.get("context", {}).get("task_id", r.get("msg_id", ""))
                            if tid:
                                result_ids.add(tid)
                        except Exception:
                            pass
        except Exception:
            pass
    return result_ids


def _iter_canonical_assignments():
    if not COORDINATION_BUS.exists():
        return
    with open(COORDINATION_BUS, "r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                message = json.loads(line)
            except Exception:
                continue
            if message.get("type") != "task_assignment":
                continue
            if message.get("from") != "factory":
                continue
            if message.get("to") not in ("anyclaw", "all"):
                continue
            yield message


def poll_once():
    """Consume canonical Factory assignments once; legacy ai/tasks is not read."""
    processed = load_processed()
    processed |= _load_result_ids()
    count = 0
    for task in _iter_canonical_assignments():
        task_id = task.get("context", {}).get("task_id", "")
        if not task_id or task_id in processed:
            continue
        valid, err = validate_task_envelope(task)
        if not valid:
            log.warning(f"Rejected invalid task: {err}")
            processed.add(task_id or task.get("msg_id", ""))
            save_processed(processed)
            continue
        lock = TaskLock(task_id)
        if not lock.try_acquire():
            log.info(f"Task {task_id[:8]}... already claimed, skipping")
            continue
        try:
            result = process_task(task)
            processed.add(task_id)
            RESULTS.parent.mkdir(parents=True, exist_ok=True)
            with open(RESULTS, "a") as f:
                f.write(json.dumps(result, default=str) + "\n")
            _publish_result_to_bus(result)
            save_processed(processed)
            emitter = get_emitter()
            if emitter:
                emitter.emit_task_completed(
                    task_id=task_id,
                    status=result['context']['status'],
                    result_summary=str(result['context'].get('result', result['context'].get('error', '')))[:200],
                    correlation_id=task.get('context', {}).get('reply_to'),
                    next_action=task.get('context', {}).get('next_action'),
                )
            count += 1
        finally:
            lock.release()
    return count


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Task Worker (canonical coordination bus)")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("poll", help="Poll canonical coordination bus once")
    loop_p = sub.add_parser("loop", help="Poll canonical coordination bus continuously")
    loop_p.add_argument("--interval", type=int, default=30)
    sub.add_parser("validate", help="Validate canonical assignments without processing")
    args = parser.parse_args()
    if args.cmd == "poll":
        print(f"Processed {poll_once()} tasks")
    elif args.cmd == "loop":
        while True:
            try:
                count = poll_once()
                if count:
                    log.info(f"Processed {count} tasks")
            except Exception as e:
                log.error(f"Error: {e}")
            time.sleep(args.interval)
    elif args.cmd == "validate":
        for task in _iter_canonical_assignments() or ():
            valid, err = validate_task_envelope(task)
            print(f"  {task.get('context', {}).get('task_id', '?')}: {'✓' if valid else '✗ ' + err}")
    else:
        parser.print_help()
