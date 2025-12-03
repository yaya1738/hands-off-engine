# === HARD SUPPRESS: legacy "Polymarket summary" ===
try:
    import requests as _rq, urllib.parse as _up
    _old_post = _rq.post
    def _patched_post(url, json=None, data=None, **kw):
        text = ""
        if isinstance(json, dict): text = json.get("text","") or text
        if isinstance(data, dict): text = data.get("text","") or text
        # also inspect URL-encoded payloads if any
        if isinstance(data, str):
            try:
                q=_up.parse_qs(data); text = q.get("text", [""])[0] or text
            except Exception: pass
        if text.startswith("📊 Polymarket summary"):
            class R: ok=True; text="suppressed"
            return R()
        return _old_post(url, json=json, data=data, **kw)
    _rq.post = _patched_post
except Exception:
    pass
# === END HARD SUPPRESS ===

# === PRELUDE: suppress legacy Polymarket summary ===
try:
    import requests as _rq
    _old_post = _rq.post
    def _patched_post(url, json=None, **kw):
        t = (json or {}).get("text","")
        if t.startswith("📊 Polymarket summary"):
            # drop legacy noisy sender, keep compact + decision
            class R: ok=True; text="suppressed"
            return R()
        return _old_post(url, json=json, **kw)
    _rq.post = _patched_post
except Exception:
    pass
# === END PRELUDE ===

# === PRELUDE: Polymarket compact (robust) ===
try:
    import os, json, requests
    from pathlib import Path
    token=os.environ.get("TOKEN") or ""
    chat_id=os.environ.get("CHAT_ID") or ""
    candidates = [
        Path("/data/data/com.termux/files/home/hands-off/state/polymarket-compact.json"),
        Path("/data/data/com.termux/files/home/hands-off/out/polymarket-compact.json"),
    ]
    src = next((c for c in candidates if c.exists()), None)
    if token and chat_id and src:
        raw = src.read_text()[:3500]
        label = "📊 Polymarket compact"
        try:
            text = f"{label}\n" + json.dumps(json.loads(raw), indent=2)[:3500]
        except Exception:
            text = f"{label} (raw)\n{raw}"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": text})
except Exception:
    pass
# === END PRELUDE ===

#!/data/data/com.termux/files/usr/bin/python
# stdlib only
import os, json, time, urllib.parse, urllib.request

HOME = os.path.expanduser("~")
env_path = os.path.join(HOME, "hands-off", "state", "tg", "bots", "handsoff.env")

def load_env(path):
    d={}
    try:
        for line in open(path, encoding="utf-8"):
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v=line.split("=",1)
            d[k.strip()]=v.strip()
    except FileNotFoundError:
        pass
    return d

def read_compact_json():
    # try a few likely locations
    candidates = [
        os.path.join(HOME, "hands-off", "agent", "polymarket-compact.json"),
        os.path.join(HOME, "hands-off", "state", "polymarket-compact.json"),
        os.path.join(HOME, "hands-off", "agent", "out", "polymarket-compact.json"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f), p
            except Exception:
                return None, p
    return None, None

def make_message(data, src_path):
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    if not data:
        return f"📊 Polymarket summary — {ts}\n(compact not found; skipped)\nPaths tried: {src_path or 'n/a'}"
    # data could be list or dict; try to summarize generically
    try:
        if isinstance(data, dict):
            markets = data.get("markets") or data.get("results") or []
        elif isinstance(data, list):
            markets = data
        else:
            markets = []
        n = len(markets)
        lines = [f"📊 Polymarket summary — {ts}", f"{n} markets in compact file"]
        # show up to 8 highlights if present
        for m in markets[:8]:
            name = m.get("question") or m.get("title") or m.get("name") or ""
            px   = m.get("price") or m.get("prob") or m.get("mark") or m.get("yes") or m.get("ev")
            if isinstance(px, float):
                try: px = round(px, 3)
                except: pass
            lines.append(f"• {name[:80]} — {px}")
        if src_path: lines.append(f"\n(src: {src_path})")
        return "\n".join(lines)
    except Exception:
        return f"📊 Polymarket summary — {ts}\n(compact parsed as raw)\n(src: {src_path})"

def tg_send(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "parse_mode":"HTML"}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "ignore")

env = load_env(env_path)
TOKEN = env.get("TOKEN","").strip()
CHAT_ID = env.get("CHAT_ID","").strip()

if not TOKEN or not CHAT_ID:
    print("ERR: missing TOKEN or CHAT_ID in", env_path)
    raise SystemExit(1)

data, src = read_compact_json()
msg = make_message(data, src)
print(tg_send(TOKEN, CHAT_ID, msg))


# --- Optional: include decision report if present ---
try:
    from pathlib import Path
    import os, requests
    dec = Path("/data/data/com.termux/files/home/hands-off/state/decision_report.json")
    token=os.environ.get("TOKEN") or ""
    chat_id=os.environ.get("CHAT_ID") or ""
    if dec.exists() and token and chat_id:
        txt="\ud83d\udccc Decision report\n" + dec.read_text()[:3500]
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": txt})
except Exception:
    pass


# --- HTTP fallback: fetch decision_report from droplet if not local ---
try:
    from pathlib import Path
    import os, requests
    dec = Path("/data/data/com.termux/files/home/hands-off/state/decision_report.json")
    token=os.environ.get("TOKEN") or ""
    chat_id=os.environ.get("CHAT_ID") or ""
    text = None
    if dec.exists():
        text = dec.read_text()[:3500]
    else:
        try:
            url = "http://138.68.103.156:8000/file/state/decision_report.json"
            r = requests.get(url, timeout=5)
            if r.ok and r.text.strip():
                text = r.text[:3500]
        except Exception:
            pass
    if text and token and chat_id:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": "📌 Decision report\n"+text})
except Exception:
    pass


# --- Polymarket compact: tolerant send (JSON or raw) ---
try:
    import os, json, requests
    from pathlib import Path
    token=os.environ.get("TOKEN") or ""
    chat_id=os.environ.get("CHAT_ID") or ""
    src = Path("/data/data/com.termux/files/home/hands-off/state/polymarket-compact.json")
    if token and chat_id and src.exists():
        raw = src.read_text()[:3500]
        label = "📊 Polymarket compact"
        try:
            pretty = json.dumps(json.loads(src.read_text()), indent=2)[:3500]
            text = f"{label}\n{pretty}"
        except Exception:
            text = f"{label} (raw)\n{raw}"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": text})
except Exception:
    pass


# --- Polymarket compact (robust): try state, then out; pretty if JSON else raw ---
try:
    import os, json, requests
    from pathlib import Path
    token=os.environ.get("TOKEN") or ""
    chat_id=os.environ.get("CHAT_ID") or ""
    candidates = [
        Path("/data/data/com.termux/files/home/hands-off/state/polymarket-compact.json"),
        Path("/data/data/com.termux/files/home/hands-off/out/polymarket-compact.json"),
    ]
    src = next((c for c in candidates if c.exists()), None)
    if token and chat_id and src:
        raw = src.read_text()[:3500]
        label = "📊 Polymarket compact"
        try:
            text = f"{label}\n" + json.dumps(json.loads(raw), indent=2)[:3500]
        except Exception:
            text = f"{label} (raw)\n{raw}"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": text})
except Exception:
    pass


# --- Compact pretty fallback via droplet ---
try:
    import os, json, requests
    token=os.environ.get("TOKEN") or ""
    chat_id=os.environ.get("CHAT_ID") or ""
    if token and chat_id:
        ok = False
        try:
            # if local pretty failed earlier, try droplet copy (always JSON now)
            r = requests.get("http://138.68.103.156:8000/file/state/polymarket-compact.json", timeout=5)
            if r.ok and r.text.strip():
                text = "📊 Polymarket compact\n" + json.dumps(json.loads(r.text), indent=2)[:3500]
                requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                              json={"chat_id": chat_id, "text": text})
                ok = True
        except Exception:
            pass
except Exception:
    pass
