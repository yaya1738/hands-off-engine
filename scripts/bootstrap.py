#!/usr/bin/env python3
"""Bootstrap all autonomous daemons with fail-closed authority."""
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
EVENT_ROUTER = REPO_ROOT / "scripts" / "event_router.py"
MONITOR = REPO_ROOT / "scripts" / "proactive_monitor.py"
TG_BRIDGE = REPO_ROOT / "scripts" / "telegram_bridge.py"
ANALYSIS = REPO_ROOT / "scripts" / "analysis_engine.py"


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


def start_daemon(name, script, args=None):
    if not script.exists():
        log_msg(f"{name} unavailable ({script.name} not found)", "WARNING")
        return None
    cmd = [sys.executable, str(script)]
    if args:
        cmd.extend(args)
    try:
        proc = subprocess.Popen(cmd, cwd=REPO_ROOT)
        log_msg(f"Started {name} (pid={proc.pid})")
        return proc
    except Exception as e:
        log_msg(f"Failed to start {name}: {e}", "ERROR")
        return None


def monitor_loop(daemons):
    restart_counts = {name: 0 for name in daemons}
    while True:
        try:
            for name, proc in list(daemons.items()):
                if proc is not None and proc.poll() is not None:
                    log_msg(f"{name} died (code={proc.returncode}), restarting", "WARNING")
                    restart_counts[name] += 1
                    if restart_counts[name] >= 10:
                        log_msg(f"Max restarts for {name}", "ERROR")
                        continue
                    wait = min(2 ** restart_counts[name], 300)
                    time.sleep(wait)
                    scripts = {
                        "governed_root": (ENTRY_POINT, None),
                        "listener": (LISTENER, None),
                        "event_router": (EVENT_ROUTER, ["loop", "--interval", "10"]),
                        "monitor": (MONITOR, ["--interval", "60"]),
                        "telegram_bridge": (TG_BRIDGE, None),
                        "analysis_engine": (ANALYSIS, None),
                    }
                    if name in scripts:
                        script, args = scripts[name]
                        daemons[name] = start_daemon(name, script, args)
                        restart_counts[name] = 0

            active = {k: v is not None and v.poll() is None for k, v in daemons.items()}
            write_status({
                "status": "running",
                "authority": "fail_closed",
                "execution_enabled": False,
                "daemons": active,
            })
            time.sleep(10)

        except KeyboardInterrupt:
            log_msg("Shutdown initiated")
            for name, proc in daemons.items():
                if proc and proc.poll() is None:
                    log_msg(f"Terminating {name}")
                    proc.terminate()
            break
        except Exception as e:
            log_msg(f"Monitor error: {e}", "ERROR")
            time.sleep(5)


# ── Main ──

log_msg("=" * 70)
log_msg("FAIL-CLOSED AUTONOMOUS BOOTSTRAP (all daemons)")

if not ENTRY_POINT.exists():
    log_msg("Governed root missing; refusing to start", "ERROR")
    write_status({"status": "blocked", "authority": "fail_closed"})
    sys.exit(1)

daemons = {
    "governed_root": start_daemon("governed_root", ENTRY_POINT),
    "listener": start_daemon("listener", LISTENER),
    "event_router": start_daemon("event_router", EVENT_ROUTER, ["loop", "--interval", "10"]),
    "monitor": start_daemon("monitor", MONITOR, ["--interval", "60"]),
    "telegram_bridge": start_daemon("telegram_bridge", TG_BRIDGE),
    "analysis_engine": start_daemon("analysis_engine", ANALYSIS),
}

active_count = sum(1 for p in daemons.values() if p and p.poll() is None)
log_msg(f"Started {active_count}/{len(daemons)} daemons")

monitor_loop(daemons)
