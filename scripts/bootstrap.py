#!/usr/bin/env python3
import sys, os, json, subprocess, time
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path.home() / "hands-off-engine"
STATE_DIR = REPO_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = STATE_DIR / "bootstrap.log"
STATUS_FILE = STATE_DIR / "autonomy_status.json"
ENTRY_POINT = REPO_ROOT / "autonomous" / "governed_root.py"
LISTENER = REPO_ROOT / "scripts" / "system_listener_inline.py"


def log_msg(msg, level="INFO"):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def write_status(status):
    status["timestamp"] = datetime.now(timezone.utc).isoformat()
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except Exception:
        pass


def start_system():
    log_msg(f"Starting governed root: {ENTRY_POINT}")
    os.chdir(REPO_ROOT)
    return subprocess.Popen([sys.executable, str(ENTRY_POINT)], cwd=REPO_ROOT)


def start_listener():
    if not LISTENER.exists():
        log_msg("Listener unavailable; continuing without it", "WARNING")
        return None
    log_msg("Starting system listener")
    try:
        proc = subprocess.Popen([sys.executable, str(LISTENER)], cwd=REPO_ROOT)
        log_msg("Listener started")
        return proc
    except Exception as e:
        log_msg(f"Listener failed: {e}", "ERROR")
        return None


def start_monitor():
    monitor = REPO_ROOT / "scripts" / "proactive_monitor.py"
    if not monitor.exists():
        log_msg("Proactive monitor unavailable", "WARNING")
        return None
    log_msg("Starting proactive monitor")
    try:
        proc = subprocess.Popen([sys.executable, str(monitor), "--interval", "60"], cwd=REPO_ROOT)
        log_msg("Monitor started")
        return proc
    except Exception as e:
        log_msg(f"Monitor failed: {e}", "ERROR")
        return None


def monitor(main_proc, listener_proc, monitor_proc=None):
    main_restarts = 0
    while True:
        try:
            if main_proc.poll() is not None:
                log_msg(f"Governed root died, code {main_proc.returncode}", "WARNING")
                main_restarts += 1
                if main_restarts < 10:
                    wait = min(2 ** main_restarts, 300)
                    log_msg(f"Restart governed root in {wait}s (attempt {main_restarts})")
                    time.sleep(wait)
                    main_proc = start_system()
                else:
                    log_msg("Max governed-root restarts reached", "ERROR")
                    break
            if listener_proc and listener_proc.poll() is not None:
                log_msg("Listener died, restarting", "WARNING")
                listener_proc = start_listener()
            if monitor_proc and monitor_proc.poll() is not None:
                log_msg("Monitor died, restarting", "WARNING")
                monitor_proc = start_monitor()
            write_status({"status": "running", "entry_point": str(ENTRY_POINT), "authority": "fail_closed", "execution_enabled": False, "main_restarts": main_restarts, "listener_active": listener_proc is not None and listener_proc.poll() is None, "monitor_active": monitor_proc is not None and monitor_proc.poll() is None})
            time.sleep(10)
        except KeyboardInterrupt:
            log_msg("Shutdown")
            main_proc.terminate()
            if listener_proc:
                listener_proc.terminate()
            if monitor_proc:
                monitor_proc.terminate()
            break
        except Exception as e:
            log_msg(f"Monitor error: {e}", "ERROR")
            time.sleep(5)


log_msg("=" * 70)
log_msg("FAIL-CLOSED AUTONOMOUS BOOTSTRAP")
log_msg("=" * 70)

if not ENTRY_POINT.exists():
    log_msg("Governed root missing; refusing to start legacy entrypoints", "ERROR")
    write_status({"status": "blocked", "authority": "fail_closed", "execution_enabled": False})
    sys.exit(1)

write_status({"status": "starting", "entry_point": str(ENTRY_POINT), "authority": "fail_closed", "execution_enabled": False})
main_proc = start_system()
listener_proc = start_listener()
monitor_proc = start_monitor()
monitor(main_proc, listener_proc, monitor_proc)
