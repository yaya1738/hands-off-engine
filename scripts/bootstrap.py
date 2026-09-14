#!/usr/bin/env python3
import sys, os, json, subprocess, time, signal
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path.home() / "hands-off-engine"
STATE_DIR = REPO_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = STATE_DIR / "bootstrap.log"
STATUS_FILE = STATE_DIR / "autonomy_status.json"

def log_msg(msg, level="INFO"):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

def write_status(status):
    status["timestamp"] = datetime.now(timezone.utc).isoformat()
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except:
        pass

def find_entry():
    for c in ["ai/unified_ai.py", "executor/autonomous_agent.py", "ai_nexus/nexus_core.py", "ai/ho_ai_loop.py"]:
        if (REPO_ROOT / c).exists():
            log_msg(f"Found: {c}")
            return str(REPO_ROOT / c)
    log_msg("No entry point!", "ERROR")
    return None

def start(ep):
    log_msg(f"Starting: {ep}")
    os.chdir(REPO_ROOT)
    return subprocess.Popen([sys.executable, ep], cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

def monitor(proc, ep):
    restarts = 0
    while True:
        try:
            if proc.poll() is not None:
                log_msg(f"System died, code {proc.poll()}", "WARNING")
                restarts += 1
                if restarts < 10:
                    wait = min(2 ** restarts, 300)
                    log_msg(f"Restart in {wait}s (attempt {restarts})", "INFO")
                    time.sleep(wait)
                    proc = start(ep)
                    restarts = 0
                else:
                    log_msg("Max restarts reached", "ERROR")
                    break
            else:
                write_status({"status": "running", "entry_point": ep, "restarts": restarts})
                time.sleep(10)
        except KeyboardInterrupt:
            log_msg("Shutdown", "INFO")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()
            break
        except Exception as e:
            log_msg(f"Error: {e}", "ERROR")
            time.sleep(5)

log_msg("="*70)
log_msg("BOOTSTRAP START")
log_msg("="*70)

ep = find_entry()
if ep:
    write_status({"status": "starting", "entry_point": ep})
    proc = start(ep)
    monitor(proc, ep)
