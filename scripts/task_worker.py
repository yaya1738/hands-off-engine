#!/usr/bin/env python3
"""
Task Worker — picks up tasks from inbox, processes them, writes results.

This is the concrete bidirectional protocol between Factory and AnyClaw:
  Factory appends to ai/tasks/inbox.jsonl  (commit to main)
  AnyClaw polls inbox, processes, appends to ai/tasks/results.jsonl (commit to main)
  Factory polls results.jsonl for its task_id
"""

import json
import sys
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [TaskWorker] %(message)s')
log = logging.getLogger("TaskWorker")

REPO_ROOT = Path.home() / "hands-off-engine"
# Allowed directories for read operations (prevents path traversal)
SAFE_READ_DIRS = [
    REPO_ROOT / "docs",
    REPO_ROOT / "ai",
    REPO_ROOT / "state",
    REPO_ROOT / "scripts",
    REPO_ROOT / "tests",
]

INBOX = REPO_ROOT / "ai" / "tasks" / "inbox.jsonl"
RESULTS = REPO_ROOT / "ai" / "tasks" / "results.jsonl"
PROCESSED_IDS = REPO_ROOT / "state" / "processed_task_ids.json"


def load_processed():
    if PROCESSED_IDS.exists():
        try:
            return set(json.loads(PROCESSED_IDS.read_text()))
        except Exception:
            pass
    return set()


def save_processed(ids):
    PROCESSED_IDS.write_text(json.dumps(list(ids)))


def process_task(task):
    """Process a single task and return a result dict."""
    task_id = task.get("context", {}).get("task_id", task.get("msg_id", "unknown"))
    action = task.get("context", {}).get("action", "unknown")
    params = task.get("context", {}).get("params", {})
    message = task.get("message", "")

    log.info(f"Processing task {task_id[:8]}... action={action}")

    try:
        if action == "health_check" or "health" in message.lower():
            result = {"status": "success", "result": {"health": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}}
        elif action == "system_status" or "status" in message.lower():
            result = {"status": "success", "result": {"system": "running", "authority": "fail_closed"}}
        elif action == "execute":
            from scripts.system_listener_inline import process_command
            cmd = {"id": task_id, "action": "execute", "mode": params.get("mode", "DRYRUN"), "payload": {"action": params.get("action", "unknown"), "params": params}}
            r = process_command(cmd)
            result = {"status": "success", "result": r}
        elif action == "list_backends":
            from scripts.ai_connector import AIConnector
            ai = AIConnector()
            result = {"status": "success", "result": ai.list_backends()}
        elif action == "read_file_fact":
            file_path = params.get("file_path", "")
            full_path = (REPO_ROOT / file_path).resolve()
            # Path traversal guard: must be under one of SAFE_READ_DIRS
            in_safe_dir = any(
                str(full_path).startswith(str(d.resolve()))
                for d in SAFE_READ_DIRS
            )
            if not in_safe_dir:
                result = {"status": "error", "error": f"Path traversal blocked: {file_path} is outside safe directories"}
            else:
                result_data = {"file_path": file_path, "file_exists": full_path.exists()}
                if full_path.exists():
                    result_data["file_size_bytes"] = full_path.stat().st_size
                    try:
                        content = full_path.read_text()[:5000]
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
        elif action == "list_parties":
            from scripts.comm_hub import CommHub
            hub = CommHub()
            result = {"status": "success", "result": [p["id"] for p in hub.list_parties()]}
        else:
            result = {"status": "success", "result": {"message": f"Received task: {message[:200]}", "action": action, "params": params}}
    except Exception as e:
        result = {"status": "error", "error": str(e)}

    return {
        "from": "anyclaw",
        "to": "factory",
        "type": "task_result",
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


def poll_once():
    """Read inbox, process new tasks, write results."""
    if not INBOX.exists():
        return 0

    processed = load_processed()
    count = 0

    with open(INBOX, "r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                task = json.loads(line)
            except Exception:
                continue

            task_id = task.get("context", {}).get("task_id", task.get("msg_id", ""))
            if task_id in processed:
                continue

            # Check if addressed to us
            to_field = task.get("to", "")
            if to_field and to_field not in ("anyclaw", "all"):
                continue

            result = process_task(task)
            processed.add(task_id)

            with open(RESULTS, "a") as f:
                f.write(json.dumps(result, default=str) + "\n")

            log.info(f"Completed task {task_id[:8]}... -> {result['context']['status']}")
            count += 1

    save_processed(processed)
    return count


def commit_changes():
    """Auto-commit results so Factory can see them."""
    try:
        subprocess.run(["git", "add", "ai/tasks/results.jsonl"], cwd=REPO_ROOT, capture_output=True, timeout=5)
        subprocess.run(["git", "commit", "-m", "coord: anyclaw task results update"],
                       cwd=REPO_ROOT, capture_output=True, timeout=10)
        subprocess.run(["git", "push", "origin", "main"], cwd=REPO_ROOT, capture_output=True, timeout=15)
    except Exception:
        pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Task Worker")
    parser.add_argument("--once", action="store_true", help="Poll once and exit")
    parser.add_argument("--loop", action="store_true", help="Poll continuously")
    parser.add_argument("--interval", type=int, default=30, help="Poll interval seconds")
    args = parser.parse_args()

    if args.once:
        count = poll_once()
        print(f"Processed {count} tasks")
        if count > 0:
            commit_changes()
    elif args.loop:
        while True:
            try:
                count = poll_once()
                if count > 0:
                    log.info(f"Processed {count} tasks, committing...")
                    commit_changes()
            except Exception as e:
                log.error(f"Error: {e}")
            time.sleep(args.interval)
    else:
        parser.print_help()
