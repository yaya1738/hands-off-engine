#!/usr/bin/env python3
import sys, os, json, subprocess, time, signal, threading
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

def start_system(ep):
    log_msg(f"Starting system: {ep}")
    os.chdir(REPO_ROOT)
    return subprocess.Popen([sys.executable, ep], cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

def start_listener():
    log_msg("Starting system listener")
    listener_py = REPO_ROOT / "scripts" / "system_listener_inline.py"
    try:
        proc = subprocess.Popen([sys.executable, str(listener_py)], cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log_msg("Listener started")
        return proc
    except Exception as e:
        log_msg(f"Listener failed: {e}", "ERROR")
        return None

def monitor(main_proc, listener_proc, entry_point):
    main_restarts = 0
    while True:
        try:
            if main_proc.poll() is not None:
                log_msg(f"System died, code {main_proc.poll()}", "WARNING")
                main_restarts += 1
                if main_restarts < 10:
                    wait = min(2 ** main_restarts, 300)
                    log_msg(f"Restart main in {wait}s (attempt {main_restarts})", "INFO")
                    time.sleep(wait)
                    main_proc = start_system(entry_point)
                    main_restarts = 0
                else:
                    log_msg("Max main restarts reached", "ERROR")
                    break
            
            if listener_proc and listener_proc.poll() is not None:
                log_msg("Listener died, restarting", "WARNING")
                listener_proc = start_listener()
            
            write_status({
                "status": "running",
                "entry_point": entry_point,
                "main_restarts": main_restarts,
                "listener_active": listener_proc is not None and listener_proc.poll() is None
            })
            
            time.sleep(10)
        except KeyboardInterrupt:
            log_msg("Shutdown", "INFO")
            main_proc.terminate()
            if listener_proc:
                listener_proc.terminate()
            break
        except Exception as e:
            log_msg(f"Monitor error: {e}", "ERROR")
            time.sleep(5)

log_msg("="*70)
log_msg("BOOTSTRAP WITH SYSTEM LISTENER")
log_msg("="*70)

ep = find_entry()
if ep:
    write_status({"status": "starting", "entry_point": ep})
    main_proc = start_system(ep)
    listener_proc = start_listener()
    monitor(main_proc, listener_proc, ep)
else:
    log_msg("Cannot start: no entry point found", "ERROR")
    sys.exit(1)
