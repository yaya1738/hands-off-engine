import sys, json, time, logging
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from autonomous.governed_authority import authorize
try:
    from scripts.executor import Executor
except ImportError:
    Executor = None
try:
    from scripts.comm_hub import CommHub
except ImportError:
    CommHub = None

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [SystemListener] %(message)s')
log = logging.getLogger("SystemListener")

REPO_ROOT = Path.home() / "hands-off-engine"
STATE_DIR = REPO_ROOT / "state"
QUEUE_FILE = STATE_DIR / "command_queue.jsonl"
RESULTS_FILE = STATE_DIR / "results.jsonl"
APPROVAL_FILE = STATE_DIR / "approval_queue.json"


def load_approval_queue():
    if APPROVAL_FILE.exists():
        try:
            return json.loads(APPROVAL_FILE.read_text())
        except Exception:
            pass
    return {"pending": [], "approved": [], "rejected": []}


def save_approval_queue(data):
    APPROVAL_FILE.write_text(json.dumps(data, indent=2) + "\n")


def process_command(cmd):
    action = cmd.get("action", "query")
    log.info(f"Processing: {action}")

    # --- governed authority gate for execute commands ---
    if action == "execute":
        decision = authorize(cmd)
        log.info(f"Authority decision for {cmd.get('id','?')}: {decision.decision} ({decision.reason})")

        if decision.decision == "rejected":
            return {"action": "execute", "error": decision.reason, "command_status": "failed", "timestamp": datetime.now(timezone.utc).isoformat()}

        if decision.decision == "approval_required":
            q = load_approval_queue()
            already_pending = any(p.get("id") == cmd.get("id") for p in q.get("pending", []))
            if not already_pending:
                q["pending"].append({
                    "id": cmd.get("id"),
                    "action": action,
                    "target": cmd.get("target"),
                    "payload": cmd.get("payload"),
                    "mode": cmd.get("mode", "DRYRUN"),
                    "queued_at": datetime.now(timezone.utc).isoformat(),
                })
                save_approval_queue(q)
            return {"action": "execute", "error": "Awaiting approval", "command_status": "awaiting_approval", "timestamp": datetime.now(timezone.utc).isoformat()}

        if decision.decision == "dryrun_only":
            log.info(f"DRYRUN: would execute {cmd.get('payload',{}).get('action','?')} but execution is not enabled")
            return {"action": "execute", "dryrun": True, "message": f"DRYRUN processed: {cmd.get('payload',{}).get('action','?')}", "timestamp": datetime.now(timezone.utc).isoformat()}

        if decision.decision == "approved":
            if Executor is not None:
                try:
                    executor = Executor()
                    exec_result = executor.execute_command(cmd)
                    status = exec_result.status
                    return {"action": "execute", "execution_result": exec_result.to_dict(), "command_status": status, "timestamp": datetime.now(timezone.utc).isoformat()}
                except Exception as e:
                    log.error(f"Executor failed: {e}")
                    return {"action": "execute", "error": str(e), "command_status": "error", "timestamp": datetime.now(timezone.utc).isoformat()}
            return {"action": "execute", "error": "Approved but executor module unavailable", "command_status": "awaiting_executor", "timestamp": datetime.now(timezone.utc).isoformat()}

    handlers = {
        "query": lambda c: {"query": c.get("payload", {}).get("query"), "response": "Query executed", "timestamp": datetime.now(timezone.utc).isoformat()},
        "status": lambda c: {"action": "status", "timestamp": datetime.now(timezone.utc).isoformat()},
        "pause": lambda c: {"action": "pause", "message": "System paused", "timestamp": datetime.now(timezone.utc).isoformat()},
        "resume": lambda c: {"action": "resume", "message": "System resumed", "timestamp": datetime.now(timezone.utc).isoformat()},
        "adjust": lambda c: {"action": "adjust", "message": "Parameter adjusted", "timestamp": datetime.now(timezone.utc).isoformat()},
    }

    handler = handlers.get(action, lambda c: {"error": f"Unknown action: {action}", "command_status": "failed", "timestamp": datetime.now(timezone.utc).isoformat()})
    return handler(cmd)


def proactive_notify():
    """Push proactive alerts about system state that needs attention."""
    if CommHub is None:
        return
    try:
        hub = CommHub()
        hub.check_and_notify()
    except Exception as e:
        log.error(f"Proactive notify failed: {e}")


if __name__ == "__main__":
    while True:
        try:
            if QUEUE_FILE.exists():
                with open(QUEUE_FILE, "r") as f:
                    lines = f.readlines()

                pending = []
                for line in lines:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get("status") == "pending":
                                pending.append(data)
                        except Exception:
                            pass

                if pending:
                    log.info(f"Found {len(pending)} pending commands")

                for cmd in pending[:5]:
                    cmd_id = cmd.get("id", "unknown")
                    try:
                        result = process_command(cmd)
                        command_status = result.pop("command_status", "completed")

                        with open(RESULTS_FILE, "a") as f:
                            f.write(json.dumps({"id": cmd_id, "status": command_status, "result": result, "timestamp": datetime.now(timezone.utc).isoformat()}) + "\n")

                        new_lines = []
                        for line in lines:
                            if line.strip():
                                try:
                                    d = json.loads(line)
                                    if d.get("id") == cmd_id:
                                        d["status"] = command_status
                                        d["result"] = result
                                    new_lines.append(json.dumps(d) + "\n")
                                except Exception:
                                    new_lines.append(line)

                        with open(QUEUE_FILE, "w") as f:
                            f.writelines(new_lines)

                        log.info(f"Finished: {cmd_id} ({command_status})")
                    except Exception as e:
                        log.error(f"Failed {cmd_id}: {e}")

            proactive_notify()
            time.sleep(5)
        except Exception as e:
            log.error(f"Error: {e}")
            time.sleep(10)
