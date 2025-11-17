#!/data/data/com.termux/files/usr/bin/python3
import os, json, subprocess, time
from pathlib import Path

BASE = Path(os.environ["HOME"]) / "hands-off"
AGENT = BASE / "agent"
STATE = BASE / "state"
OUT = BASE / "out"
LOGDIR = Path(os.environ["HOME"]) / ".cron-logs"
MASTER = STATE / "master.json"

LOGDIR.mkdir(parents=True, exist_ok=True)
STATE.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    with open(LOGDIR / "orchestrator.log", "a") as f:
        f.write(f"[{ts}] " + msg + "\n")

def run(cmd):
    try:
        out = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True
        )
        log(f"[ok] {cmd}")
        return out.strip()
    except subprocess.CalledProcessError as e:
        log(f"[err] {cmd}\n{e.output}")
        return None

# -----------------------------------
# 1) Run data fetchers
# -----------------------------------
run(f"python3 {AGENT}/fetcher.py")
run(f"python3 {AGENT}/pm_trim.py")

# -----------------------------------
# 2) Push to Telegram + IFTTT
# -----------------------------------
run(f"python3 {AGENT}/pm_tg_push.py")
run(f"bash {AGENT}/pm_ifttt_push.sh")

# -----------------------------------
# 3) Build master.json
# -----------------------------------
master = {
    "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
    "fetcher_json": str(OUT / "fetch-latest.json") if (OUT / "fetch-latest.json").exists() else None,
    "pm_compact": str(STATE / "polymarket-compact.json") if (STATE / "polymarket-compact.json").exists() else None,
}

with open(MASTER, "w") as f:
    json.dump(master, f, indent=2)

log("[ok] master.json updated")

# -----------------------------------
# 4) Touch .last_ok to trigger mirror/decider
# -----------------------------------
MIRROR = BASE / "mirror"
MIRROR.mkdir(parents=True, exist_ok=True)
LASTOK = MIRROR / ".last_ok"
LASTOK.write_text(str(time.time()))

log("[ok] .last_ok touched")
