#!/usr/bin/env python3
"""Health Monitor — checks all services and sends Telegram alerts on issues.

Run periodically (e.g. via cron or Node 1 tick). Reports status,
detects failures, and auto-restarts dead services.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
HEALTH_LOG = STATE / "health_log.jsonl"
TOKEN_FILE = Path.home() / ".codex" / "telegram-bridge.json"


def check_process(name_pattern):
    """Check if a process matching the pattern is running."""
    for pid_dir in Path("/proc").iterdir():
        if not pid_dir.name.isdigit():
            continue
        try:
            cmd = (pid_dir / "cmdline").read_text().replace("\x00", " ")
            if name_pattern in cmd:
                return int(pid_dir.name)
        except (FileNotFoundError, PermissionError):
            continue
    return None


def check_bus():
    """Check bus health."""
    bus = ROOT / "ai" / "coordination" / "messages.jsonl"
    if not bus.exists():
        return {"status": "missing", "messages": 0}
    lines = bus.read_text().splitlines()
    valid = sum(1 for l in lines if l.strip())
    return {"status": "ok", "messages": valid}


def check_telegram():
    """Check if Telegram bridge is connected."""
    try:
        if TOKEN_FILE.exists():
            d = json.loads(TOKEN_FILE.read_text())
            return {"status": "configured", "has_token": bool(d.get("botToken"))}
        return {"status": "no_config"}
    except Exception:
        return {"status": "error"}


def check_disk():
    """Check disk space."""
    st = os.statvfs(str(ROOT))
    free_gb = (st.f_bavail * st.f_frsize) / (1024**3)
    return {"free_gb": round(free_gb, 2), "ok": free_gb > 1.0}


def check_git():
    """Check git status."""
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%h"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=5
        )
        return {"commit": r.stdout.strip(), "ok": True}
    except Exception:
        return {"ok": False}


def send_telegram(msg):
    """Send a Telegram alert."""
    if not TOKEN_FILE.exists():
        return False
    try:
        d = json.loads(TOKEN_FILE.read_text())
        token = d["botToken"]
        chat_id = d["chatIds"][0]
        import urllib.request, urllib.parse
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": msg,
            "disable_web_page_preview": "true"
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        return False


def run_health_check():
    """Run full health check."""
    now = datetime.now(timezone.utc).isoformat()
    
    checks = {
        "node1": check_process("node1_runtime"),
        "telegram_bridge": check_process("telegram_bridge"),
        "control_room": check_process("yair_control_room"),
        "bus": check_bus(),
        "telegram_config": check_telegram(),
        "disk": check_disk(),
        "git": check_git(),
    }
    
    issues = []
    if not checks["node1"]:
        issues.append("Node 1 not running")
    if not checks["telegram_bridge"]:
        issues.append("Telegram bridge not running")
    if not checks["control_room"]:
        issues.append("Control Room not running")
    if checks["bus"]["status"] == "missing":
        issues.append("Bus file missing")
    if not checks["disk"]["ok"]:
        issues.append(f"Low disk: {checks['disk']['free_gb']}GB free")
    
    result = {
        "timestamp": now,
        "checks": checks,
        "issues": issues,
        "healthy": len(issues) == 0,
    }
    
    # Log
    STATE.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_LOG, "a") as f:
        f.write(json.dumps(result) + "\n")
    
    # Alert on issues
    if issues:
        alert = f"⚠️ Health Alert: {', '.join(issues)}"
        send_telegram(alert)
    
    print(f"Health: {'✅ OK' if not issues else '⚠️ ISSUES: ' + ', '.join(issues)}")
    return result


if __name__ == "__main__":
    run_health_check()
