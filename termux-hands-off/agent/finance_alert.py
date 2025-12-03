import json, os, sys, pathlib, hashlib, time
from datetime import datetime, timezone
import urllib.request, urllib.parse

HERE = pathlib.Path(__file__).parent.resolve()
HOME = os.path.expanduser("~")
BASE_OUT = f"{HOME}/hands-off-out"
STATE = f"{BASE_OUT}/state"
LAST = f"{STATE}/alerts_last.json"
ALERTS_ENV = f"{HOME}/hands-off/state/alerts.env"
LAST_ALERT_META = f"{STATE}/last_alert_meta.json"
ALERTS_LOG = f"{STATE}/alerts_log.jsonl"

def env_from_file(path):
    d={}
    if not os.path.exists(path): return d
    for line in open(path, encoding="utf-8", errors="ignore"):
        if "=" in line:
            k,v = line.split("=",1)
            v = v.split("#",1)[0].strip().strip('"').strip("'")
            d[k.strip()] = v
    return d

def _num(d, k, default):
    raw = str(d.get(k, default))
    raw = raw.split("#",1)[0].strip().strip('"').strip("'")
    try: return float(raw) if raw else float(default)
    except: return float(default)

def money(x):
    try:
        x = float(x)
        return f"${x:,.0f}" if abs(x)>=100 else f"${x:,.2f}"
    except: return str(x)

def load_json(p):
    try:
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def pct(delta, base):
    try:
        base = float(base)
        if base == 0: return None
        return 100.0*float(delta)/base
    except: return None

def send_tg(text):
    tg = env_from_file(f"{HOME}/hands-off/state/tg/bots/handsoff.env")
    token = tg.get("TOKEN") or tg.get("BOT_TOKEN") or tg.get("TG_TOKEN")
    chat  = tg.get("CHAT_ID") or tg.get("TG_CHAT_ID")
    if not token or not chat: return False
    data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
        return True
    except:
        return False

def send_ifttt(text, title="Finance Alert", value2=""):
    env = env_from_file(f"{HOME}/hands-off/state/ifttt.env")
    hook = env.get("IFTTT_WEBHOOK") or env.get("WEBHOOK")
    if not hook: return False
    payload = json.dumps({"value1": text, "value2": value2, "value3": ""}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(hook, data=payload, headers={"Content-Type":"application/json"}), timeout=10)
        return True
    except:
        return False

def load_sources():
    try:
        with open(f"{STATE}/finance.json","r",encoding="utf-8") as f:
            fin=json.load(f)
    except: fin={}
    try:
        with open(f"{STATE}/decision_report.json","r",encoding="utf-8") as f:
            rep=json.load(f)
    except: rep={}
    return fin, rep

def snapshot_key(fin):
    acc = fin.get("accounts",{}) or {}
    return {"net": fin.get("net_usd"),
            "acc": {k: (acc.get(k,{}).get("balance")) for k in sorted(acc.keys())}}

def diff_snap(now, prev):
    out={"net": None, "accounts": {}}
    if now.get("net") is not None and prev.get("net") is not None:
        out["net"] = now["net"] - prev["net"]
    for k,v in (now.get("acc",{}) or {}).items():
        pv = (prev.get("acc",{}) or {}).get(k)
        if v is not None and pv is not None:
            out["accounts"][k] = v - pv
    return out

def hour_local():
    try: return datetime.now().hour
    except: return 0

def calc_liquid(fin, match_csv):
    acc = (fin.get("accounts") or {})
    toks = [t.strip().lower() for t in (match_csv or "").split(",") if t.strip()]
    if not toks: return 0.0
    s = 0.0
    for name, obj in acc.items():
        bal = (obj or {}).get("balance")
        if bal is None: continue
        n = str(name).lower()
        if any(t in n for t in toks):
            try: s += float(bal)
            except: pass
    return s

def shield_allows(msg, window_min, max_log):
    """Return True if we should send msg; implements dedupe window & logs."""
    try:
        meta = load_json(LAST_ALERT_META)
    except: meta={}
    now = time.time()
    # hash by message body only (stable)
    h = hashlib.sha256(msg.encode("utf-8")).hexdigest()[:16]
    last_h = meta.get("hash")
    last_ts = float(meta.get("ts", 0))
    if window_min>0 and h == last_h and (now - last_ts) < (window_min*60):
        return False
    # write new meta
    try:
        with open(LAST_ALERT_META,"w",encoding="utf-8") as f:
            json.dump({"hash": h, "ts": now}, f)
    except: pass
    # append log line
    try:
        os.makedirs(os.path.dirname(ALERTS_LOG), exist_ok=True)
        with open(ALERTS_LOG,"a",encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "msg": msg})+"\n")
        # truncate if over limit
        if int(max_log)>0:
            with open(ALERTS_LOG,"r",encoding="utf-8") as f:
                lines=f.readlines()
            if len(lines)>int(max_log):
                with open(ALERTS_LOG,"w",encoding="utf-8") as f:
                    f.writelines(lines[-int(max_log):])
    except: pass
    return True

def main():
    args = sys.argv[1:]
    mini = ("--mini-report" in args)

    cfg = env_from_file(ALERTS_ENV)
    d_usd  = _num(cfg, "DELTA_THRESHOLD_USD", 500.0)
    d_pct  = _num(cfg, "DELTA_THRESHOLD_PCT", 1.5)
    a_usd  = _num(cfg, "ACCOUNT_DELTA_USD", 250.0)
    a_pct  = _num(cfg, "ACCOUNT_DELTA_PCT", 3.0)
    crit   = _num(cfg, "CRITICAL_DELTA_USD", 0.0)
    liquid_match = cfg.get("LIQUID_MATCH","")
    cash_min = _num(cfg, "CASH_MIN_USD", 0.0)
    daily_burn = _num(cfg, "DAILY_BURN_USD", 0.0)
    min_days = _num(cfg, "CASH_MIN_DAYS", 0.0)
    quiet  = (cfg.get("QUIET_HOURS","") or "").split(",")
    qhrs   = set([h.strip() for h in quiet if h.strip().isdigit()])
    shield_min = _num(cfg, "SPAM_SHIELD_MIN", 0.0)
    max_log = int(_num(cfg, "ALERTS_LOG_MAX", 500))

    fin, rep = load_sources()
    if not fin:
        if mini:
            print("[mini] no finance.json"); sys.exit(0)
        else:
            sys.exit(0)

    now_key = snapshot_key(fin)
    try: last = json.load(open(LAST,"r",encoding="utf-8"))
    except: last = {}
    delta = diff_snap(now_key, last) if last else {"net": None, "accounts": {}}

    lines=[]; reasons=[]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    net = fin.get("net_usd")
    net_p=None
    if delta["net"] is not None and last.get("net"):
        net_p = pct(delta["net"], last["net"])

    if mini:
        lines.append(f"📊 Finance — {ts}")
        lines.append(f"Net: {money(net) if net is not None else '-'}")
        if net_p is not None:
            lines.append(f"Δ since last: {money(delta['net'])} ({net_p:.2f}%)")
        tops=[]
        for k,v in (delta.get("accounts") or {}).items():
            base = (last.get("acc",{}) or {}).get(k)
            pp = pct(v, base)
            tops.append((abs(v), f"{k}: {money(v)}" + (f" ({pp:.2f}%)" if pp is not None else "")))
        tops.sort(reverse=True)
        if tops: lines.append("Top movers: " + "; ".join([t[1] for t in tops[:5]]))
        liq = calc_liquid(fin, liquid_match)
        want_cash = max(cash_min, (daily_burn*min_days if (daily_burn>0 and min_days>0) else 0))
        if liq is not None:
            lines.append(f"Liquid: {money(liq)}" + (f" / target ≥ {money(want_cash)}" if want_cash>0 else ""))
        msg="\n".join(lines)
        sent_tg = send_tg(msg); sent_if = send_ifttt(msg, title="Finance Mini", value2="mini")
        with open(LAST,"w",encoding="utf-8") as f: json.dump(now_key, f)
        print(f"[mini] tg={sent_tg} ifttt={sent_if}"); return

    in_quiet = str(hour_local()) in qhrs
    fired=False

    if crit>0 and delta["net"] is not None and abs(delta["net"]) >= crit:
        reasons.append("critical"); fired=True; in_quiet=False

    if not fired and delta["net"] is not None and last.get("net"):
        net_hit = (abs(delta["net"]) >= d_usd) or (net_p is not None and abs(net_p) >= d_pct)
        if net_hit: reasons.append("net"); fired=True

    acc_lines=[]
    for k,v in (delta.get("accounts") or {}).items():
        base = (last.get("acc",{}) or {}).get(k)
        pp = pct(v, base)
        if abs(v) >= a_usd or (pp is not None and abs(pp) >= a_pct):
            acc_lines.append(f"{k}: {money(v)}" + (f" ({pp:.2f}%)" if pp is not None else ""))
    if acc_lines: reasons.append("accounts"); fired=True

    liq = calc_liquid(fin, liquid_match)
    want_cash = max(cash_min, (daily_burn*min_days if (daily_burn>0 and min_days>0) else 0))
    if want_cash>0 and liq < want_cash:
        reasons.append("cash buffer"); fired=True

    if fired:
        head = f"📈 Finance Alert — {ts}"
        if reasons: head += " [" + ", ".join(reasons) + "]"
        body=[]
        if "critical" in reasons and delta["net"] is not None:
            dp = (f" ({pct(delta['net'], last.get('net')):.2f}%)" if last.get('net') else "")
            body.append(f"CRITICAL Δ: {money(delta['net'])}{dp}")
        elif delta["net"] is not None and last.get("net"):
            body.append(f"Net Δ: {money(delta['net'])}" + (f" ({net_p:.2f}%)" if net_p is not None else ""))
        if acc_lines: body.append("Accounts: " + "; ".join(sorted(acc_lines)))
        if "cash buffer" in reasons: body.append(f"Liquid {money(liq)} < target {money(want_cash)}")
        body.append(f"Net now: {money(net) if net is not None else '-'}")
        msg = head + "\n" + "\n".join(body)

        # spam-shield + log
        if shield_allows(msg, shield_min, max_log):
            send_tg(msg); send_ifttt(msg, title="Finance Alert", value2="delta")

    with open(LAST,"w",encoding="utf-8") as f: json.dump(now_key, f)

if __name__ == "__main__":
    main()
