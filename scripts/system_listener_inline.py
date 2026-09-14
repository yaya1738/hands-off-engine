import sys, json, time, logging
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [SystemListener] %(message)s')
log = logging.getLogger("SystemListener")

REPO_ROOT = Path.home() / "hands-off-engine"
STATE_DIR = REPO_ROOT / "state"
QUEUE_FILE = STATE_DIR / "command_queue.jsonl"
RESULTS_FILE = STATE_DIR / "results.jsonl"

def process_command(cmd):
    action = cmd.get("action", "query")
    log.info(f"Processing: {action}")
    
    handlers = {
        "query": lambda c: {"query": c.get("payload", {}).get("query"), "response": "Query executed", "timestamp": datetime.now(timezone.utc).isoformat()},
        "status": lambda c: {"action": "status", "timestamp": datetime.now(timezone.utc).isoformat()},
        "pause": lambda c: {"action": "pause", "message": "System paused", "timestamp": datetime.now(timezone.utc).isoformat()},
        "resume": lambda c: {"action": "resume", "message": "System resumed", "timestamp": datetime.now(timezone.utc).isoformat()},
        "execute": lambda c: {"action": "execute", "error": "No governed execution authority is bound", "command_status": "failed", "timestamp": datetime.now(timezone.utc).isoformat()},
        "adjust": lambda c: {"action": "adjust", "message": "Parameter adjusted", "timestamp": datetime.now(timezone.utc).isoformat()}
    }
    
    handler = handlers.get(action, lambda c: {"error": f"Unknown action: {action}", "command_status": "failed", "timestamp": datetime.now(timezone.utc).isoformat()})
    return handler(cmd)

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
                    except:
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
                            except:
                                new_lines.append(line)
                    
                    with open(QUEUE_FILE, "w") as f:
                        f.writelines(new_lines)
                    
                    log.info(f"Finished: {cmd_id} ({command_status})")
                except Exception as e:
                    log.error(f"Failed {cmd_id}: {e}")
        
        time.sleep(5)
    except Exception as e:
        log.error(f"Error: {e}")
        time.sleep(10)
