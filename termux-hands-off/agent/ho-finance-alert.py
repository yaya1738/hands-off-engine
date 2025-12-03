#!/usr/bin/env python3
import json
import os
from pathlib import Path
from urllib import request, parse, error
from math import isfinite

FINANCE_URL = "http://138.68.103.156:8001/file/finance_report.json"

HOME = Path.home()
STATE_DIR = HOME / "hands-off" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

LAST_FILE = STATE_DIR / "finance_last.json"
TG_ENV = STATE_DIR / "tg.env"

# thresholds
MIN_ABS_DELTA_USD = 25.0     # only alert if move >= $25
MIN_REL_DELTA_PCT = 2.0      # or >= 2% change

def load_finance():
    try:
        with request.urlopen(FINANCE_URL, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[warn] failed to fetch finance_report.json: {e}")
        return None

    if not isinstance(data, dict):
        print("[warn] finance_report.json is not a dict")
        return None

    total = data.get("total_usd")
    prev = data.get("prev_usd", None)
    if total is None:
        print("[warn] finance_report missing total_usd")
        return None

    return {
        "raw": data,
        "total_usd": float(total),
        "prev_usd": float(prev) if prev is not None else None,
    }

def load_last():
    if not LAST_FILE.exists():
        return None
    try:
        with LAST_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[warn] failed to read {LAST_FILE}: {e}")
        return None

def save_last(snapshot):
    try:
        with LAST_FILE.open("w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, sort_keys=True)
    except Exception as e:
        print(f"[warn] failed to write {LAST_FILE}: {e}")

def load_tg_env():
    if not TG_ENV.exists():
        print(f"[warn] no tg.env at {TG_ENV}, skipping Telegram")
        return None, None

    token = None
    chat_id = None

    for line in TG_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k == "TG_BOT_TOKEN":
            token = v
        elif k == "TG_CHAT_ID":
            chat_id = v

    if not token or not chat_id:
        print("[warn] TG_BOT_TOKEN or TG_CHAT_ID missing in tg.env")
        return None, None

    return token, chat_id

def send_tg_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    data = parse.urlencode(payload).encode("utf-8")
    try:
        with request.urlopen(url, data=data, timeout=10) as resp:
            _ = resp.read()
        print("[ok] Telegram alert sent")
    except error.HTTPError as e:
        print(f"[warn] Telegram HTTP {e.code}: {e.read()!r}")
    except Exception as e:
        print(f"[warn] Telegram send failed: {e}")

def main():
    now = load_finance()
    if not now:
        return

    total = now["total_usd"]
    if not isfinite(total):
        print("[warn] total_usd is not finite, aborting")
        return

    last = load_last()
    if not last:
        print("[info] no previous snapshot, saving baseline only")
        save_last({
            "total_usd": total,
            "raw": now["raw"],
        })
        return

    prev_total = float(last.get("total_usd", total))
    delta = total - prev_total
    rel_pct = (delta / prev_total * 100.0) if prev_total else 0.0

    print(f"[info] prev_total={prev_total:.2f}, total={total:.2f}, delta={delta:.2f} ({rel_pct:.2f}%)")

    if abs(delta) < MIN_ABS_DELTA_USD and abs(rel_pct) < MIN_REL_DELTA_PCT:
        print("[info] change below thresholds, no alert")
        return

    direction = "up" if delta > 0 else "down"
    sign = "+" if delta > 0 else ""
    msg = (
        "*FINANCE ALERT*\n"
        f"Total: *${total:,.2f}* (was ${prev_total:,.2f})\n"
        f"Change: *{sign}${delta:,.2f}* ({rel_pct:+.2f}% {direction})\n"
    )

    token, chat_id = load_tg_env()
    if token and chat_id:
        send_tg_message(token, chat_id, msg)
    else:
        print("[info] Telegram not configured, skipping send")

    save_last({
        "total_usd": total,
        "raw": now["raw"],
    })

if __name__ == "__main__":
    main()
