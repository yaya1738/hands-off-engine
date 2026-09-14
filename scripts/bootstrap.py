#!/usr/bin/env python3
import sys, os, json, subprocess, time
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
            log_msg(f"Found entry: {c}")
            return str(REPO_ROOT / c)
    return None

def start_process(script, name):
    log_msg(f"Starting {name}: {script}")
    os.chdir(REPO_ROOT)
    return subprocess.Popen([sys.executable, script], cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

def monitor(processes, ep):
    restarts = {name: 0 for name in processes.keys()}
    while True:
        try:
            for name, proc in processes.items():
                if proc and proc.poll() is not None:
                    log_msg(f"{name} died, code {proc.poll()}", "WARNING")
                    restarts[name] += 1
                    if restarts[name] < 10:
                        wait = min(2 ** restarts[name], 300)
                        log_msg(f"Restarting {name} in {wait}s", "INFO")
                        time.sleep(wait)
                        script = str(REPO_ROOT / "scripts" / f"{name}.py" if name != "main" else ep)
                        processes[name] = start_process(script, name)
                        restarts[name] = 0
            
            active = sum(1 for p in processes.values() if p and p.poll() is None)
            write_status({
                "status": "running",
                "entry_point": ep,
                "processes_active": active,
                "processes_total": len(processes),
                "processes": {k: (v.poll() is None if v else False) for k, v in processes.items()},
                "restarts": restarts
            })
            time.sleep(10)
        except KeyboardInterrupt:
            log_msg("Shutdown", "INFO")
            for proc in processes.values():
                if proc:
                    proc.terminate()
            break
        except Exception as e:
            log_msg(f"Monitor error: {e}", "ERROR")
            time.sleep(5)

log_msg("="*70)
log_msg("BOOTSTRAP: HANDS-OFF-ENGINE + GROK + CHATGPT + OPENCLAW")
log_msg("EXPONENTIAL COMPOUNDING LOOP WITH MULTI-AI COORDINATION")
log_msg("="*70)

ep = find_entry()
if ep:
    write_status({"status": "starting", "entry_point": ep})
    
    processes = {
        "main": start_process(ep, "main_system"),
        "listener": start_process(str(REPO_ROOT / "scripts" / "system_listener_inline.py"), "system_listener"),
        "analysis": start_process(str(REPO_ROOT / "scripts" / "analysis_engine.py"), "analysis_engine"),
        "coordinator": start_process(str(REPO_ROOT / "scripts" / "multi_ai_coordinator.py"), "multi_ai_coordinator")
    }
    
    log_msg(f"All processes started. Monitoring {len(processes)} systems.")
    monitor(processes, ep)
else:
    log_msg("No entry point found", "ERROR")
    sys.exit(1)
