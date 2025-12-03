#!/data/data/com.termux/files/usr/bin/python3
import os, json, time, subprocess, calendar
from pathlib import Path

HOME = Path(os.environ["HOME"])
BASE = HOME / "hands-off"
STATE = BASE / "state"
LOGDIR = HOME / ".cron-logs"

MASTER = STATE / "master.json"
STATUS = STATE / "orchestrator_watchdog_status.json"

LOGDIR.mkdir(parents=True, exist_ok=True)

THRESHOLD_MIN = 45  # how old master.json can be before we scream

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    with open(LOGDIR / "orchestrator_watchdog.log", "a") as f:
        f.write(f"[{ts}] {msg}\n")

def load_status():
    if not STATUS.exists():
        return {"status": "unknown"}
    try:
        return json.loads(STATUS.read_text())
    except Exception:
        return {"status": "unknown"}

def save_status(status):
    STATUS.write_text(json.dumps(status, indent=2))

def send_telegram(msg):
    tg_dir = STATE / "tg" / "bots"
    env_file = tg_dir / "handsoff.env"
    if not env_file.exists():
        log("[warn] telegram env not found")
        return
    env = {}
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    token = env.get("TOKEN")
    chat_id = env.get("CHAT_ID")
    if not token or not chat_id:
        log("[warn] telegram TOKEN/CHAT_ID missing")
        return
    try:
        subprocess.check_output(
            [
                "curl", "-s", "-X", "POST",
                f"https://api.telegram.org/bot{token}/sendMessage",
                "-d", f"chat_id={chat_id}",
                "-d", f"text={msg}"
            ],
            stderr=subprocess.STDOUT
        )
        log("[ok] telegram alert sent")
    except subprocess.CalledProcessError as e:
        log(f"[err] telegram alert failed: {e.output}")

def send_ifttt(msg):
    env_file = STATE / "ifttt.env"
    if not env_file.exists():
        log("[warn] ifttt.env not found")
        return
    env = {}
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    url = env.get("IFTTT_WEBHOOK")
    if not url:
        log("[warn] IFTTT_WEBHOOK missing")
        return
    try:
        subprocess.check_output(
            [
                "curl", "-s", "-X", "POST", url,
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"value1": "orchestrator_watchdog", "value2": msg})
            ],
            stderr=subprocess.STDOUT
        )
        log("[ok] ifttt alert sent")
    except subprocess.CalledProcessError as e:
        log(f"[err] ifttt alert failed: {e.output}")

# ---------------- main ----------------
status = load_status()

if not MASTER.exists():
    msg = "Hands-Off alert: master.json missing (orchestrator may not have run yet)."
    if status.get("status") != "missing":
        send_telegram(msg)
        send_ifttt(msg)
    save_status({"status": "missing", "ts": time.time()})
    log("[warn] master.json missing")
    raise SystemExit(0)

try:
    data = json.loads(MASTER.read_text())
    ts_str = data.get("timestamp_utc")
    ts_struct = time.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    ts = calendar.timegm(ts_struct)
except Exception as e:
    msg = f"Hands-Off alert: cannot parse master.json timestamp: {e}"
    if status.get("status") != "bad_timestamp":
        send_telegram(msg)
        send_ifttt(msg)
    save_status({"status": "bad_timestamp", "ts": time.time()})
    log("[err] bad master.json timestamp")
    raise SystemExit(0)

age_min = (time.time() - ts) / 60.0
log(f"[info] master.json age = {age_min:.1f} min")

if age_min > THRESHOLD_MIN:
    msg = f"Hands-Off alert: orchestrator stale (master.json age {age_min:.1f} min > {THRESHOLD_MIN} min)."
    if status.get("status") != "stale":
        send_telegram(msg)
        send_ifttt(msg)
    save_status({"status": "stale", "ts": time.time(), "age_min": age_min})
    log("[warn] orchestrator stale")
else:
    # Only log transition back to healthy once
    if status.get("status") not in ("ok", "unknown"):
        msg = f"Hands-Off: orchestrator healthy again (age {age_min:.1f} min)."
        send_telegram(msg)
        send_ifttt(msg)
    save_status({"status": "ok", "ts": time.time(), "age_min": age_min})
    log("[ok] orchestrator healthy")
